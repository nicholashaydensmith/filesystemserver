class ServerError extends Error {
  constructor(message) {
    super(message);
    this.name = "ServerError";
  }
}

const fetch_json = (url) => fetch(url).then(response => { if (response.ok) return response.json(); throw new ServerError(response.statusText); } );

const fetch_text = (url) => fetch(url).then(response => { if (response.ok) return response.text(); throw new ServerError(response.statusText); } );

const error_handler = (error) => {
  console.log(error);
  document.body.innerHTML =
    `<div style="font-family: ui-monospace, courier new, monospace">
      <h1>${error}</h1>
      <blockquote><pre>${error.stack}</pre></blockquote>
    </div>`;
};

const fss = {
  query: (callback, queries = ["cwd", "list", "plugins"]) => {
    query = queries.map(q => `query=${q}`).join("&");
    fetch_json(`?${query}`)
      .then(callback)
      .catch(error_handler);
  },

  download: (url, callback) => {
    const fetch_fn = url.endsWith(".json") ? fetch_json : fetch_text;
    fetch_fn(`?download=${url}`)
      .then(callback)
      .catch(error_handler);
  },
}
