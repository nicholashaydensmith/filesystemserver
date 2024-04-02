# filesystemserver / `fss`

`filesystemserver` is a python package, out of the box is just `python3 -m http.server 8080`, but its superpower is its extensible plugin system.

`filesystemserver` plugins can be loaded on the fly (or automatically) to serve your file system files/directories as rich content, some examples might include:
- Serving a directory full of images as an image gallery
- Serving data stored in json or csv files as a chart or interactive visualization
- Serving a directory containing git repo with Monaco code editor

`filesystemserver` installs a CLI wrapper called `fss`.

## Install
```bash
pip install filesystemserver
```

## Usage
`fss` has three subcommands `serve` (default), `install`, and `update`. `fss` with no arguments will launch a server for the current directory and serves on default `port` and `address` (see config section below for changing defaults):

```bash
fss
```

### Plugin Installation
```bash
# Github project path (git clone)
fss install nicholashaydensmith/gallery.fss

# Or full URL (to any git host endpoint)
fss install https://github.com/nicholashaydensmith/gallery.fss.git
```

### Plugin Update
```bash
# Update a specific plugin (git pull)
fss update nicholashaydensmith/gallery.fss

# Update all installed plugins
fss update
```

## `fss` Configuration

`fss` is configured via toml `~/.config/fss/config.toml` and has the following options:
```toml
address = "localhost"
port = 8080
default_plugin = "fss/browser"
```

## Developing a Plugin

The simplest possible plugin is just a git project with an `index.html` file.  Plugins are installed into `~/.config/fss/plugin`.

### `index.html`

### JavaScript API

### `fss.toml`

### Examples
- https://github.com/nicholashaydensmith/gallery.fss
- https://github.com/nicholashaydensmith/highlight.fss

## Development

`filesystemserver` itself strives to be as small and simple as possible, leaving all features and extensibility to plugins.

It also strives to have as few dependencies as possible, currently its only dependency requirement is for python pre 3.11 package `tomli`.
