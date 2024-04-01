function app_main(data) {
  console.log(data);
  const dirlist = data["list"];
  const plugins = data["plugins"];
  const container = document.getElementById("container");
  const root = (dirlist.root == "/") ? dirlist.root : dirlist.root + "/";
  const [_, h1] = dirlist.root.split("/").reduce((a, c) => {
    const [url_part, h1_part] = a;
    const url_sep = url_part.length > 1 ? "/" : "";
    const href_sep = url_part.length > 0 ? "/" : "";
    c = url_part.length > 0 ? c : "/";
    const url = `${url_part}${url_sep}${c}`;
    return [url, `${h1_part}${href_sep}<a href="?cwd=${url}">${c}</a>`];
  }, ["", ""]);
  const list = dirlist.paths.map((p, i) => `<li><a href="?cwd=${root}${p}">${p}</a><span class="nav" id="${i}"> >> </span></li>`).join("");
  container.innerHTML = `<h1>${h1}<span class="nav"> >> </span></h1><ul>${list}</ul>`;

  const plugin_container = document.getElementById("plugin_container");
  const collection = container.getElementsByClassName("nav");
  for (let e of collection) {
    e.addEventListener("mouseover", (i) => {
      const rect = i.target.getBoundingClientRect();
      const plugin_list = plugins.length > 0
        ? plugins.map(p => `<li><a href="/${p}?cwd=${root}${i.target.id === "" ? "" : dirlist.paths.at(i.target.id)}">${p}</a></li>`).join("")
        : "<em>No plugins installed</em>";
      plugin_container.style.display = "block";
      plugin_container.style.left = rect.right + "px";
      plugin_container.style.top = (rect.top - 5) + "px";
      plugin_container.innerHTML = `<ul style="list-style-type: none; padding: 5px; margin: 0px;">${plugin_list}</ul>`;
    });
  }

  plugin_container.addEventListener("mouseleave", (e) => plugin_container.style.display = "none");
}
