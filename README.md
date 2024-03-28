# fsserver (File System Server)

`fsserver` is a python package, out of the box is just `python3 -m http.server 8080`, but its superpower is its extensible plugin system.

`fsserver` plugins can be loaded on the fly (or automatically) to serve your file system files/directories as rich content, some examples might include:
- Serving a directory full of images as an image gallery
- Serving data stored in json or csv files as a chart or interactive visualization
- Serving a directory containing git repo with Monaco code editor

`fsserver` installs a CLI wrapper called `fss`.

## Install
```bash
pip install fsserver
```

## Plugin Installation
```bash
# Github project path
fss install nicholashaydensmith/gallery.fss

# Or full URL (to any git host endpoint)
fss install https://github.com/nicholashaydensmith/gallery.fss.git
```
