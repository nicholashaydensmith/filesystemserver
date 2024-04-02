import argparse
import glob
import http.server
import importlib.resources
import io
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import urllib.parse

if (
    sys.version_info.major,
    sys.version_info.minor,
) < (3, 11):
    import tomli as toml
else:
    import tomllib as toml


def resolve_git_repo(url):
    if not url.startswith("http"):
        url = f"https://github.com/{url}"
    plugin_dir = "/".join(url.split("/")[-2:])
    return url, plugin_dir


def installed_plugins(plugin_dir):
    index = "index.html"
    prefix_len = len(plugin_dir) + 1
    postfix_len = len(index) + 1
    plugins = []
    for m in glob.glob(f"{plugin_dir}/**/{index}", recursive=True):
        directory = m[prefix_len:-postfix_len]
        plugin = {"name": directory}
        config_path = os.path.join(plugin_dir, directory, "fss.toml")
        if os.path.exists(config_path):
            with open(config_path, "rb") as fd:
                plugin.update(toml.load(fd))
        plugin["directory"] = directory
        plugins.append(plugin)
    return sorted(plugins, key=lambda m: m["name"])


def git(*args, cwd=None, help_message=""):
    assert cwd is not None
    try:
        subprocess.run(["git", "-C", cwd, *args], check=True)
    except FileNotFoundError:
        print(
            "Error: git command not found, git is required for plugin install / update",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError:
        print(f"Error: {help_message}", file=sys.stderr)
        sys.exit(1)


def install(args):
    repo, plugin_dir = resolve_git_repo(args.plugin)
    git(
        "clone",
        repo,
        plugin_dir,
        cwd=args.plugin_dir,
        help_message="Perhaps the plugin specified is already installed, did you mean to run `update`?",
    )
    print("Succesfully installed:", plugin_dir)


def update(args):
    plugins = (
        args.plugins if len(args.plugins) > 0 else installed_plugins(args.plugin_dir)
    )
    for plugin in plugins:
        repo, plugin_dir = resolve_git_repo(plugin["directory"])
        cwd = os.path.join(args.plugin_dir, plugin_dir)
        if not os.path.exists(os.path.join(cwd, ".git")):
            print(
                "Warning: plugin is not git repo, skipping:",
                plugin_dir,
                file=sys.stderr,
            )
            continue
        git(
            "pull",
            cwd=cwd,
            help_message="Perhaps the plugin isn't already installed, did you mean to run `install`?",
        )
        print("Succesfully updated:", plugin_dir)


def serve(args):
    class PluginRequestHandler(http.server.BaseHTTPRequestHandler):
        cwd = "/"

        def send_file(
            self, f, fsize, ctype, encoding=None, last_modified=None, revalidate=False
        ):
            self.send_response(http.server.HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fsize))
            if encoding is not None:
                self.send_header("Content-Encoding", encoding)
            if last_modified is not None:
                self.send_header("Last-Modified", last_modified)
            if revalidate:
                self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return f

        def send_as_json(self, d):
            text_io = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
            json.dump(d, text_io)
            f = text_io.detach()
            fsize = f.tell()
            f.seek(0)
            return self.send_file(f, fsize, "application/json")

        def send_file_at_path(self, path, revalidate=False):
            if not os.path.exists(path):
                return self.send_error(
                    http.server.HTTPStatus.NOT_FOUND, f"File not found {path}"
                )
            if os.path.isdir(path):
                return self.send_error(
                    http.server.HTTPStatus.BAD_REQUEST,
                    f"File attempting to open is directory {path}",
                )
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None:
                ctype = "application/octet-stream"
            f = open(path, "rb")
            fs = os.fstat(f.fileno())
            return self.send_file(
                f,
                fs[6],
                ctype,
                encoding=encoding,
                last_modified=self.date_time_string(fs.st_mtime),
                revalidate=revalidate,
            )

        def redirect(self, url):
            self.send_response(http.server.HTTPStatus.FOUND)
            self.send_header("Location", url)
            self.end_headers()

        @staticmethod
        def query_list():
            fspath = os.path.realpath(args.directory + PluginRequestHandler.cwd)
            return {
                "list": {
                    "root": PluginRequestHandler.cwd,
                    "paths": (
                        sorted(os.listdir(fspath)) if os.path.isdir(fspath) else []
                    ),
                }
            }

        @staticmethod
        def query_plugins():
            index = "index.html"
            prefix_len = len(args.plugin_dir) + 1
            postfix_len = len(index) + 1
            return {"plugins": installed_plugins(args.plugin_dir)}

        def plugin_handler(self, plugin_path):
            base_plugin_dir = (
                args.builtin_plugin_dir
                if plugin_path.startswith("/fss")
                else args.plugin_dir
            )
            full_plugin_path = base_plugin_dir + plugin_path
            if os.path.isdir(full_plugin_path):
                if not full_plugin_path.endswith("/"):
                    return self.redirect(plugin_path + "/")
                full_plugin_path = os.path.join(full_plugin_path, "index.html")
            return self.send_file_at_path(
                full_plugin_path, revalidate=full_plugin_path.endswith("index.html")
            )

        def query_handler(self, query_str):
            qs = urllib.parse.parse_qs(query_str)
            if "cwd" in qs:
                PluginRequestHandler.cwd = qs["cwd"][0]

            if "download" in qs:
                url = qs["download"][0]
                if url[0] != "/":
                    url = os.path.join(PluginRequestHandler.cwd, url)
                fspath = os.path.realpath(args.directory + url)
                return self.send_file_at_path(fspath)

            if "query" in qs:
                d = {}
                for q in qs["query"]:
                    if q == "list":
                        d.update(PluginRequestHandler.query_list())
                    elif q == "plugins":
                        d.update(PluginRequestHandler.query_plugins())
                    elif q == "cwd":
                        d.update({"cwd": PluginRequestHandler.cwd})
                    else:
                        return self.send_error(
                            http.server.HTTPStatus.BAD_REQUEST,
                            message=f'Unknown query "{q}"',
                        )
                return self.send_as_json(d)

        def do_HEAD(self):
            req = urllib.parse.urlparse(self.path)
            self.log_message("%s", req)
            plugin_path = req.path

            if req.query:
                f = self.query_handler(req.query)
                if f is not None:
                    return f

            if plugin_path == "/":
                PluginRequestHandler.cwd = "/"
                return self.redirect(args.default_plugin + "/")
            elif not req.query:
                return self.redirect(plugin_path + f"?cwd={PluginRequestHandler.cwd}")
            else:
                return self.plugin_handler(plugin_path)

        def do_GET(self):
            f = self.do_HEAD()
            if f:
                try:
                    shutil.copyfileobj(f, self.wfile)
                finally:
                    f.close()

    http.server.HTTPServer(
        (args.address, args.port), PluginRequestHandler
    ).serve_forever()


def get_default_fss_subpath(sub):
    config_dir = os.environ.get("XDG_CONFIG_HOME", f"{os.path.expanduser('~')}/.config")
    return f"{config_dir}/fss/{sub}"


def get_default_config_file_path():
    return get_default_fss_subpath("config.toml")


def get_default_config():
    return {
        "address": "localhost",
        "port": 8080,
        "default_plugin": "fss/browser",
    }


def load_config(config_path, create=False):
    config = get_default_config()
    if os.path.exists(config_path):
        with open(config_path, "rb") as fd:
            config.update(toml.load(fd))
    return config


def setup_defaults_and_environment(args):
    is_default_config_path = args.config_path is None
    if is_default_config_path:
        args.config_path = get_default_config_file_path()
    config = load_config(args.config_path, create=is_default_config_path)
    for k, v in config.items():
        if not hasattr(args, k) or getattr(args, k) is None:
            setattr(args, k, v)
    os.makedirs(args.plugin_dir, exist_ok=True)
    args.directory = os.path.realpath(args.directory)
    with importlib.resources.path("filesystemserver", "data") as data:
        args.builtin_plugin_dir = os.path.join(data, "plugin")
    return args


def main():
    parser = argparse.ArgumentParser(description="File System Server")
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        dest="config_path",
        help="Configuration file",
    )
    parser.add_argument(
        "-d",
        "--plugin-dir",
        default=get_default_fss_subpath("plugin"),
        help="Directory where plugins will be installed",
    )
    parser.set_defaults(func=serve, address=None, port=None, directory=".")

    subparsers = parser.add_subparsers(help="sub-command help")

    install_parser = subparsers.add_parser(
        "install",
        aliases=["i"],
        help="""install a plugin
    - either github project path `nicholashaydensmith/gallery.fss`
    - or full git URL `https://github.com/nicholashaydensmith/gallery.fss.git`""",
    )
    install_parser.set_defaults(func=install)
    install_parser.add_argument(
        "plugin",
        help="plugin to install",
    )

    update_parser = subparsers.add_parser(
        "update", aliases=["u"], help="update installed plugins"
    )
    update_parser.set_defaults(func=update)
    update_parser.add_argument(
        "plugins",
        nargs="*",
        help="plugin(s) to update",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        aliases=["s"],
        help="serve a directory",
    )
    serve_parser.set_defaults(func=serve)
    serve_parser.add_argument(
        "-a",
        "--address",
        default=None,
        help="Address to serve on",
    )
    serve_parser.add_argument(
        "-p",
        "--port",
        default=None,
        type=int,
        help="Port to serve on",
    )
    serve_parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Root directory to serve",
    )
    serve_parser.add_argument(
        "--default-plugin",
        default=None,
        help="Default plugin to launch with, default (fss/browser)",
    )

    args = setup_defaults_and_environment(parser.parse_args())
    exit_code = args.func(args)
    if exit_code is not None:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
