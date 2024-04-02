let fss = (() => {
  class FSSError extends Error {
    constructor(message) {
      super(message);
      this.name = "FSSError";
    }
  }

  const response_as_json = (r) => r.json();
  const response_as_text = (r) => r.text();

  const fetch_as = (url, as_fn) => fetch(url).then(response => { if (response.ok) return as_fn(response); throw new FSSError(response.statusText); } );
  const fetch_json = (url) => fetch_as(url, response_as_json);
  const fetch_text = (url) => fetch_as(url, response_as_text);

  const error_handler = (error) => {
    console.log(error);
    document.body.innerHTML =
      `<div style="font-family: ui-monospace, courier new, monospace">
        <h1>${error}</h1>
        <blockquote><pre>${error.stack}</pre></blockquote>
      </div>`;
  };

  const query = (callback, queries = ["cwd", "list", "plugins"]) => {
    const query_str = queries.map(q => `query=${q}`).join("&");
    fetch_json(`?${query_str}`)
      .then(callback)
      .catch(error_handler);
  };

  const download = (url, callback, as_fn = undefined) => {
    if (as_fn === undefined) {
      as_fn = url.endsWith(".json") ? response_as_json : response_as_text;
    }
    fetch_as(`?download=${url}`, as_fn)
      .then(callback)
      .catch(error_handler);
  };

  const with_data = (callback, as_fn = undefined) => {
    query(q => {
      download(q["list"].root, callback, as_fn);
    }, queries = ["list"]);
  };

  return {
    query: query,
    download: download,
    with_data: with_data,
  };
})();
