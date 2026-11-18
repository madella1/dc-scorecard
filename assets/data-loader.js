/* Loads the scorecard's data files and gives the page the same small API it used inside Claude. */
window.dash = (function () {
  const base = document.currentScript.dataset.base;
  const files = JSON.parse(document.currentScript.dataset.files);
  const D = {}; const fns = [];
  Object.keys(files).forEach((id) => { D[id] = { status: 'loading', data: [], columns: [] }; });
  const fire = () => fns.forEach((f) => { try { f(); } catch (e) { console.error(e); } });
  if (window.__DCS_DATA) { Object.assign(D, window.__DCS_DATA); }
  else Object.entries(files).forEach(([id, name]) => {
    fetch(base + name).then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); }).then((txt) => {
      if (/\.json$/.test(name)) { const data = JSON.parse(txt); D[id] = { status: 'ok', data, columns: data.length ? Object.keys(data[0]) : [] }; }
      else { const data = d3.csvParse(txt); D[id] = { status: 'ok', data: Array.from(data), columns: data.columns }; }
    }).catch(() => { D[id] = { status: 'error', data: [], columns: [] }; }).finally(fire);
  });
  let t = null;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(fire, 150); });
  const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return {
    data: (id) => D[id] || { status: 'missing', data: [], columns: [] },
    onData: (fn) => { fns.push(fn); fn(); },
    colors: [dark ? '#7ea3e6' : '#2b5ba8', '#d9822b', '#2f9e8f', '#a05fc9', '#c94f6d', '#7a8a2e', '#4f7fa8', '#9c6b3f'],
    setLink: (name) => { try { history.replaceState(null, '', '#' + name); } catch (e) {} },
    params: () => ({}), setParams: () => {}, resetParams: () => {}, refresh: () => {}
  };
})();
