// Shared helpers for the StreetSphere dashboard. Paths are relative so the same pages work on
// the dev server (Oxygen serves matching .json routes) and on a static host under any subpath.
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
  return r.json();
}
const fmt = (x, d = 2) => (x === null || x === undefined || Number.isNaN(x)) ? "—" : (+x).toFixed(d);
const pct = (x, d = 1) => (x === null || x === undefined) ? "—" : (100 * x).toFixed(d);

const isDark = () => matchMedia("(prefers-color-scheme: dark)").matches;

// --- palette (validated reference; see dataviz method) --------------------------------------
// Categorical slots in FIXED order — regions/overlays index into this, never cycle new hues.
const SERIES = () => isDark()
  ? ["#3987e5", "#008300", "#d55181", "#c98500", "#199e70", "#d95926", "#9085e9", "#e66767"]
  : ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"];
const REGION_SLOT = { north_america: 0, europe: 1, latin_america: 2, asia: 3, oceania: 4, africa_me: 5 };
const regionColor = (region) => SERIES()[REGION_SLOT[region] ?? 7];

// Sequential (magnitude) scale: ONE hue, light→dark; near-zero recedes toward the surface.
// Dark mode is its own stepped ramp (recedes into the dark surface), not a flip.
function seqScale() {
  return isDark()
    ? [[0, "#0d366b"], [0.25, "#184f95"], [0.5, "#2a78d6"], [0.75, "#6da7ec"], [1, "#cde2fb"]]
    : [[0, "#cde2fb"], [0.25, "#9ec5f4"], [0.5, "#5598e7"], [0.75, "#256abf"], [1, "#0d366b"]];
}
const seriesMain = () => SERIES()[0];

// Plotly template that follows the OS light/dark theme.
function plotlyLayout(extra = {}) {
  const dark = isDark();
  const fg = dark ? "#e6e8ec" : "#1b1e24", grid = dark ? "#262b36" : "#e2e5ea";
  return Object.assign({
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: fg, size: 12 }, margin: { l: 40, r: 12, t: 30, b: 34 },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
  }, extra);
}
const PLOT_CFG = { displayModeBar: false, responsive: true };

// Local equirectangular projection scale — the JS mirror of Julia's _cell_of constants.
// Single source per language: every map overlay derives meters-per-degree from here.
const M_PER_LAT = 110574;
const mPerLon = lat => 111320 * Math.cos(lat * Math.PI / 180);

// LineMeasure edges → bin centers (JS mirror of measures.jl midpoints).
const binCenters = edges => edges.slice(0, -1).map((lo, i) => (lo + edges[i + 1]) / 2);

// Sortable table: render `rows` into `tableEl` given column specs
// [{k, t, tip?, d?, s: row=>value, cell?: row=>html}]; click headers to sort. Returns render().
function sortableTable(tableEl, cols, rows, { sortKey = cols[0].k, asc = false,
                                              filter = null, onRender = null } = {}) {
  function render() {
    const col = cols.find(c => c.k === sortKey);
    const shown = filter ? rows.filter(filter) : rows;
    const sorted = [...shown].sort((a, b) => {
      let x = col.s(a), y = col.s(b);
      if (typeof x === "string") return asc ? x.localeCompare(y) : y.localeCompare(x);
      x = x ?? -Infinity; y = y ?? -Infinity;
      return asc ? x - y : y - x;
    });
    tableEl.querySelector("thead").innerHTML = "<tr>" + cols.map(c =>
      `<th data-k="${c.k}" title="${c.tip ?? ""}" class="${c.k === sortKey ? "sorted " + (asc ? "asc" : "") : ""}">${c.t}</th>`).join("") + "</tr>";
    tableEl.querySelector("tbody").innerHTML = sorted.map(r => "<tr>" + cols.map(c =>
      `<td>${c.cell ? c.cell(r) : fmt(c.s(r), c.d)}</td>`).join("") + "</tr>").join("");
    tableEl.querySelectorAll("th").forEach(th => th.onclick = () => {
      const k = th.dataset.k;
      if (k === sortKey) asc = !asc; else { sortKey = k; asc = false; }
      render();
    });
    onRender && onRender(sorted.length);
  }
  render();
  return render;
}

// Mini bearing-rose as inline SVG: one <path>, 36 wedge subpaths, r ∝ √weight
// (area-proportional), north-up clockwise, bidirectional mirror. Used by gallery + city pages.
function roseSVG(props, { size = 110, fill = seriesMain() } = {}) {
  const n = props.length, R = 50, wmax = Math.max(...props, 1e-12);
  let d = "";
  for (let i = 0; i < n; i++) {
    for (const half of [0, 180]) {
      const w = props[i];
      if (w <= 0) continue;
      const r = R * Math.sqrt(w / wmax);
      const t0 = ((i - 0.5) * 360 / n + half) * Math.PI / 180;
      const t1 = ((i + 0.5) * 360 / n + half) * Math.PI / 180;
      d += `M0 0 L${(r * Math.sin(t0)).toFixed(1)} ${(-r * Math.cos(t0)).toFixed(1)} ` +
           `A${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${(r * Math.sin(t1)).toFixed(1)} ${(-r * Math.cos(t1)).toFixed(1)} Z `;
    }
  }
  return `<svg viewBox="-55 -55 110 110" width="${size}" height="${size}">` +
         `<circle r="50" fill="none" stroke="var(--line)"/>` +
         `<path d="${d}" fill="${fill}" fill-opacity="0.85"/></svg>`;
}
