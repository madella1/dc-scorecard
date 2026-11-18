"""Build the public website folder. usage: build_site.py SCRATCHPAD"""
import csv, json, math, os, shutil, sys
SP = sys.argv[1]; O = SP + '/out'; S = SP + '/site'
if os.path.exists(S): shutil.rmtree(S)
for d in ('assets', 'data/traffic-safety', 'traffic-safety', 'about', 'pipeline'):
    os.makedirs(f'{S}/{d}', exist_ok=True)

SITE = 'DC Scorecard'
UPDATED = 'October 24, 2026'
NEWSLETTER = ''  # e.g. 'https://www.yourdomain.com' once the Substack is live; the nav link appears when this is set
city = next(csv.DictReader(open(O + '/dc-crashes-city.csv')))
cw = next(csv.DictReader(open(O + '/dc-crashes-citywide.csv')))
wards = {r['ward']: r for r in csv.DictReader(open(O + '/dc-crashes-by-ward.csv'))}
outl = json.load(open(O + '/dc-district-outlines.json'))

# ---------- data ----------
FILES = {'anc': 'dc-crashes-by-anc.csv', 'smd': 'dc-crashes-by-smd.csv', 'ward': 'dc-crashes-by-ward.csv', 'city': 'dc-crashes-city.csv',
         'citywide': 'dc-crashes-citywide.csv', 'peers': 'dc-peer-cities.csv', 'outlines': 'dc-district-outlines.json', 'roads': 'dc-major-roads.json'}
for f in FILES.values(): shutil.copy(f'{O}/{f}', f'{S}/data/traffic-safety/{f}')
shutil.copy(SP + '/npm/package/dist/d3.min.js', S + '/assets/d3-7.8.5.min.js')
for f in ('process.py', 'trend.py', 'build.py', 'grade.py', 'build_site.py'):
    shutil.copy(f'{SP}/scripts/{f}', f'{S}/pipeline/{f}')

# ---------- the DC flag mark: three stars over two bars ----------
def star(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.382
        pts.append(f'{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}')
    return 'M' + 'L'.join(pts) + 'Z'
FLAG = ('<svg class="flag" viewBox="0 0 40 26" aria-hidden="true" focusable="false"><path fill="currentColor" d="'
        + star(9, 5.2, 4.6) + star(20, 5.2, 4.6) + star(31, 5.2, 4.6) + 'M0 11.5H40V16.5H0ZM0 20H40V25H0Z"/></svg>')

# ---------- shared styles ----------
css = r'''/* DC Scorecard. Public Sans throughout; flag red for identity, Potomac blue for data. */
:root { color-scheme: light;
  --red: #c8102e; --ink: #15171c; --paper: #f4f5f7; --panel: #ffffff; --line: #d8dbe1; --muted: #545b67; --data: #2b5ba8;
  --color-bg: var(--paper); --color-panel: var(--panel); --color-fg: var(--ink); --color-fg-muted: var(--muted); --color-border-line: var(--line);
  --color-bad: #b4231f; --color-ok: #23753a; --color-warn: #9a6400; --color-accent: var(--data);
  --cds-chart-muted: #d3d7de; --cds-chart-grid: #e8eaee; --cds-chart-axis: #b4b9c2; --cds-text-secondary: var(--muted);
  --cds-surface-popover: #ffffff; --cds-border: var(--line); --cds-shadow-popover: 0 6px 20px rgba(21,23,28,.14);
  --font-anthropic-sans: "Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  --font-anthropic-serif: "Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  --cds-font-size-caption: .8125rem; --cds-font-size-body: .9375rem; --cds-font-size-heading: 1.0625rem; --cds-font-size-title: 1.625rem;
  --cds-font-weight-medium: 600; --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 20px; --cds-gap-xl: 28px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 16px; --cds-radius: 6px; --cds-dur-slow: 300ms; }
@media (prefers-color-scheme: dark) { :root { color-scheme: dark;
  --red: #f0566a; --ink: #e9ebef; --paper: #111317; --panel: #1a1d23; --line: #343842; --muted: #a2a8b3; --data: #7ea3e6;
  --color-bad: #f08a7a; --color-ok: #7cc68d; --color-warn: #e2b04e;
  --cds-chart-muted: #3d424c; --cds-chart-grid: #262a31; --cds-chart-axis: #555b66;
  --cds-surface-popover: #23272e; --cds-shadow-popover: 0 6px 20px rgba(0,0,0,.5); } }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--font-anthropic-sans); font-size: var(--cds-font-size-body); line-height: 1.55; }
a { color: inherit; text-underline-offset: 3px; text-decoration-thickness: 1px; }
a:focus-visible, button:focus-visible, input:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
.wrap { max-width: 1240px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.flag { display: block; color: var(--red); }

/* header, with the flag's two bars as the rule beneath it */
.site-head { background: var(--panel); }
.site-head .wrap { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 24px; padding-block: 14px; }
.brand { display: inline-flex; align-items: center; gap: 12px; text-decoration: none; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.01em; }
.brand .flag { width: 34px; height: auto; }
.site-nav { display: flex; flex-wrap: wrap; gap: 4px 22px; font-size: .875rem; }
.site-nav a { text-decoration: none; color: var(--muted); padding: 4px 0; border-bottom: 2px solid transparent; }
.site-nav a:hover { color: var(--ink); }
.site-nav a[aria-current="page"] { color: var(--ink); font-weight: 700; border-bottom-color: var(--red); }
.bars { height: 11px; background: linear-gradient(var(--red) 0 4px, transparent 4px 7px, var(--red) 7px 11px); }

main.wrap { padding-block: 28px 56px; }
.dash-skeleton { color: transparent !important; background: var(--cds-chart-muted); border-radius: 4px; }
.page-note { font-size: var(--cds-font-size-caption); color: var(--muted); margin: 0 0 14px; }

/* footer */
.site-foot { background: var(--ink); color: var(--paper); }
@media (prefers-color-scheme: dark) { .site-foot { background: #0b0c0f; color: var(--ink); } }
.site-foot .wrap { padding-block: 28px 36px; display: grid; gap: 14px; grid-template-columns: auto 1fr; align-items: start; }
.site-foot .flag { width: 44px; color: #f0566a; }
.site-foot p { margin: 0; font-size: .8125rem; opacity: .82; max-width: 80ch; }
.site-foot p + p { margin-top: 4px; }

/* home: hero */
.hero { display: grid; gap: 28px 48px; grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr); align-items: center; margin-bottom: 44px; }
@media (max-width: 820px) { .hero { grid-template-columns: 1fr; } }
.hero h1 { font-weight: 800; font-size: clamp(2.2rem, 5.2vw, 3.6rem); line-height: 1.02; letter-spacing: -0.035em; margin: 0 0 16px; text-wrap: balance; }
.hero p { margin: 0 0 22px; color: var(--muted); font-size: 1.0625rem; max-width: 58ch; }
.find { display: flex; flex-wrap: wrap; gap: 8px; max-width: 30rem; }
.find label { flex-basis: 100%; font-size: .875rem; font-weight: 600; }
.find input { flex: 1 1 14rem; min-width: 0; font: inherit; padding: 10px 12px; border: 1px solid var(--line); border-radius: var(--cds-radius); background: var(--panel); color: var(--ink); }
.find button { font: inherit; font-weight: 700; padding: 10px 18px; border: 0; border-radius: var(--cds-radius); background: var(--red); color: #fff; cursor: pointer; }
.find button:hover { filter: brightness(1.08); }
.find small { flex-basis: 100%; color: var(--muted); font-size: .8125rem; }
.hero-map { display: grid; justify-items: center; pointer-events: none; user-select: none; }
.hero-map svg { width: 100%; max-width: 400px; height: auto; display: block; overflow: visible; }
.hero-map path { fill: none; vector-effect: non-scaling-stroke; stroke-linejoin: round; stroke-linecap: round; }
.hero-map .hm-land { fill: color-mix(in oklab, var(--data) 9%, var(--panel)); }
.hero-map .hm-anc { stroke: color-mix(in oklab, var(--data) 22%, var(--panel)); stroke-width: 0.8; }
.hero-map .hm-ward { stroke: color-mix(in oklab, var(--data) 45%, var(--panel)); stroke-width: 1.3; }
.hero-map .hm-art { stroke: var(--red); stroke-width: 1.2; opacity: .55; }
.hero-map .hm-fwy { stroke: var(--red); stroke-width: 2.4; opacity: .9; }
.hero-map .hm-edge { stroke: var(--ink); stroke-width: 2; }
@media (prefers-reduced-motion: no-preference) {
  .hero-map .hm-road { stroke-dasharray: 1; stroke-dashoffset: 1; animation: hm-draw 2.4s cubic-bezier(.4, 0, .2, 1) .2s forwards; }
  .hero-map .hm-fwy { animation-delay: .9s; }
  @keyframes hm-draw { to { stroke-dashoffset: 0; } }
}

/* home: the report card */
.rc-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 20px; margin-bottom: 10px; }
.rc-head h2 { margin: 0; font-size: 1.375rem; font-weight: 800; letter-spacing: -0.015em; }
.rc-head p { margin: 0; color: var(--muted); font-size: .875rem; }
.report { background: var(--panel); border: 1px solid var(--line); border-top: 4px solid var(--red); border-radius: var(--cds-radius); margin-bottom: 44px; }
.rc-row { display: grid; grid-template-columns: minmax(10rem, 1fr) minmax(0, 2.4fr) minmax(0, 1.4fr) 7.5rem; gap: 6px 24px; align-items: center; padding: 16px 20px; border-top: 1px solid var(--line); text-decoration: none; color: inherit; }
.rc-row:first-child { border-top: 0; }
.rc-cols { padding-block: 10px; font-size: .8125rem; color: var(--muted); font-weight: 600; }
a.rc-row:hover { background: color-mix(in oklab, var(--data) 5%, var(--panel)); }
.rc-subj { display: grid; gap: 4px; justify-items: start; }
.rc-subj b { font-size: 1.0625rem; font-weight: 700; }
.rc-what { color: var(--muted); font-size: .9rem; }
.rc-src { color: var(--muted); font-size: .8125rem; }
.rc-grade { justify-self: end; text-align: right; display: grid; gap: 2px; justify-items: end; }
.rc-letter { font-weight: 800; font-size: 2.25rem; line-height: 1; letter-spacing: -0.02em; }
.rc-letter-sub { font-size: .75rem; color: var(--muted); }
.rc-none { font-size: .8125rem; color: var(--muted); }
.tag { font-size: .75rem; font-weight: 600; border-radius: 999px; padding: 1px 9px; border: 1px solid var(--line); color: var(--muted); }
.tag.live { color: var(--color-ok); border-color: currentColor; }
.rc-open { font-size: .8125rem; font-weight: 700; color: var(--red); }
@media (max-width: 760px) {
  .rc-cols { display: none; }
  .rc-row { grid-template-columns: 1fr auto; padding: 14px 16px; }
  .rc-subj { grid-column: 1; grid-row: 1; }
  .rc-grade { grid-column: 2; grid-row: 1 / span 2; }
  .rc-what, .rc-src { grid-column: 1; }
}

/* home: explainer */
.explain { display: grid; gap: 24px 40px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr)); border-top: 1px solid var(--line); padding-top: 28px; }
.explain h3 { margin: 0 0 6px; font-size: 1rem; font-weight: 700; }
.explain p { margin: 0; color: var(--muted); font-size: .9375rem; max-width: 60ch; }

/* about */
.prose { max-width: 70ch; display: grid; gap: 14px; }
.prose h1 { font-weight: 800; font-size: clamp(1.9rem, 4vw, 2.6rem); letter-spacing: -0.03em; line-height: 1.08; margin: 0 0 4px; }
.prose h2 { font-size: 1.125rem; font-weight: 700; margin: 14px 0 0; }
.prose p, .prose li { margin: 0; color: var(--muted); }
.prose b { color: var(--ink); }
.prose ul { margin: 0; padding-left: 1.1rem; display: grid; gap: 6px; }

/* scorecard page tweaks: grade letters and the panel name pick up the site's heavier type */
.cs-title { font-weight: 800 !important; letter-spacing: -0.03em; }
.cs-panel-name { font-weight: 700 !important; letter-spacing: -0.015em; }
.cs-grade-letter { font-weight: 800; letter-spacing: -0.02em; }
.cs-tabs button[aria-selected="true"] { border-bottom-color: var(--red) !important; }
'''
open(S + '/assets/site.css', 'w').write(css)

# ---------- data loader (stands in for the dashboard runtime) ----------
shim = r'''/* Loads the scorecard's data files and gives the page the same small API it used inside Claude. */
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
'''
open(S + '/assets/data-loader.js', 'w').write(shim)

# Public Sans (SIL Open Font License), self-hosted so the site makes no third-party requests
os.makedirs(S + '/assets/fonts', exist_ok=True)
FONTCSS = ''
for wt in (400, 600, 700, 800):
    shutil.copy(f'{SP}/npmfont/package/files/public-sans-latin-{wt}-normal.woff2', f'{S}/assets/fonts/public-sans-{wt}.woff2')
    FONTCSS += f"@font-face {{ font-family: 'Public Sans'; font-style: normal; font-weight: {wt}; font-display: swap; src: url('fonts/public-sans-{wt}.woff2') format('woff2'); }}\n"
open(S + '/assets/site.css', 'w').write(FONTCSS + css)
FONTS = ''
FIXLINKS = r'''<script>
/* Opened straight from disk: folder links need index.html added (a web server does this automatically) */
if (location.protocol === 'file:') {
  const fix = (u) => u.replace(/^([^?#]*\/|\.\/?|)(?=[?#]|$)/, (m) => (m === '' || m === '.' || m === './' ? './' : m) + 'index.html');
  document.querySelectorAll('a[href]').forEach((a) => { const h = a.getAttribute('href'); if (!/^[a-z]+:/i.test(h) && !h.startsWith('#')) a.setAttribute('href', fix(h)); });
  document.querySelectorAll('form[action]').forEach((f) => { f.setAttribute('action', fix(f.getAttribute('action'))); });
}
</script>'''
NAV = [('/', 'Home'), ('/traffic-safety/', 'Traffic safety'), ('/about/', 'About')]
def shell(title, desc, body, current, extra_head='', root='/'):
    nav = ''.join(f'<a href="{(root + h.lstrip("/")) or "./"}"{" aria-current=\"page\"" if h == current else ""}>{t}</a>' for h, t in NAV)
    if NEWSLETTER: nav += f'<a href="{NEWSLETTER}">Newsletter</a>'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="theme-color" content="#c8102e">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="{root}assets/site.css">
{extra_head}
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="{root or './'}">{FLAG}<span>{SITE}</span></a>
  <nav class="site-nav" aria-label="Main">{nav}</nav>
</div></header>
<div class="bars" aria-hidden="true"></div>
<main class="wrap">
{body}
</main>
<footer class="site-foot"><div class="wrap">
  {FLAG}
  <div>
    <p>{SITE} is an independent, nonpartisan project that grades how DC is doing using the District's own public data. It is not affiliated with the DC government.</p>
    <p>Sources and methods are listed on each scorecard. Last updated {UPDATED}.</p>
  </div>
</div></footer>
{FIXLINKS}
</body>
</html>
'''
open(S + '/assets/favicon.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="6" fill="#fff"/><path fill="#c8102e" transform="translate(0 7)" d="'
    + star(9, 5.2, 4.6) + star(20, 5.2, 4.6) + star(31, 5.2, 4.6) + 'M0 11.5H40V16.5H0ZM0 20H40V25H0Z"/></svg>')

# ---------- traffic safety page ----------
# The same data as one script file, so the page also works when opened straight from disk (browsers block file fetches there)
EMB = {}
for k, f in FILES.items():
    if f.endswith('.json'):
        d = json.load(open(f'{O}/{f}')); EMB[k] = {'status': 'ok', 'data': d, 'columns': list(d[0].keys()) if d else []}
    else:
        r = csv.DictReader(open(f'{O}/{f}')); d = list(r); EMB[k] = {'status': 'ok', 'data': d, 'columns': r.fieldnames}
open(f'{S}/data/traffic-safety/data.js', 'w').write('window.__DCS_DATA = ' + json.dumps(EMB, separators=(',', ':')) + ';\n')
page = open(O + '/index.html').read()
head = f'''<script src="../assets/d3-7.8.5.min.js"></script>
<script src="../data/traffic-safety/data.js"></script>
<script src="../assets/data-loader.js" data-base="../data/traffic-safety/" data-files='{json.dumps(FILES)}'></script>'''
deeplink = '''<script>
/* ?q=4D02 from the home page search opens that area's scorecard */
(function () {
  const q = new URLSearchParams(location.search).get('q'); if (!q) return;
  let done = false;
  dash.onData(() => {
    if (done || dash.data('smd').status !== 'ok' || dash.data('anc').status !== 'ok' || dash.data('outlines').status !== 'ok') return;
    done = true;
    const f = document.getElementById('cs-find'); f.value = q;
    setTimeout(() => { f.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); document.getElementById('map').scrollIntoView({ block: 'start' }); }, 50);
  });
})();
</script>'''
body = f'<p class="page-note">Crash data through {cw["data_through"]}. Updated {UPDATED}.</p>\n' + page + deeplink
open(S + '/traffic-safety/index.html', 'w').write(shell(f'Traffic safety scorecard | {SITE}', 'Safety grades for every DC ward, ANC and single-member district, built from police crash reports and DDOT traffic counts.', body, '/traffic-safety/', head, root='../'))

# ---------- home ----------
# Decorative map: DC's outline, its ANC and ward lines, and the major roads in flag red. No data, no links.
roads = json.load(open(O + '/dc-major-roads.json'))
lv = lambda name: [o for o in outl if o['level'] == name]
W, H = float(outl[0]['map_w']), float(outl[0]['map_h'])
# outer edge only: the merged outline has tiny slivers between districts that would show as stray marks
city_p = 'M' + max(lv('city')[0]['path'].split('M')[1:], key=len)
anc_p = ''.join(o['path'] for o in lv('anc'))
ward_p = ''.join(o['path'] for o in lv('ward'))
# one element per road segment so each draws in over the full animation
segs = lambda codes: ''.join(f'<path class="hm-road {cls}" pathLength="1" d="M{d}"/>' for r in roads if int(r['class_code']) in codes
                             for cls in ['hm-fwy' if int(r['class_code']) < 3 else 'hm-art'] for d in r['path'].split('M') if d)
art_p = segs((3,)); fwy_p = segs((1, 2))
hero_map = f'''<div class="hero-map" aria-hidden="true">
  <svg viewBox="-12 -12 {W + 24:.0f} {H + 24:.0f}" focusable="false">
    <path class="hm-land" d="{city_p}"/>
    <path class="hm-anc" d="{anc_p}"/>
    <path class="hm-ward" d="{ward_p}"/>
    <g>{art_p}</g>
    <g>{fwy_p}</g>
    <path class="hm-edge" d="{city_p}"/>
  </svg>
</div>'''

CATS = [
    ('Traffic safety', 'live', 'traffic-safety/', 'People hurt or killed in crashes, pedestrians and cyclists hit, and how risky the streets are for the traffic they carry.', 'Police crash reports, DDOT traffic counts'),
    ('Public safety', 'planned', None, 'Reported crime by type, per resident and over time, for each ward and neighborhood.', 'MPD crime incidents'),
    ('City services', 'planned', None, 'How quickly 311 requests are resolved, by service and neighborhood, and whether that is improving.', '311 service requests'),
    ('Affordability', 'planned', None, 'Rents and home prices against local incomes, and how many households pay too much for housing.', 'Census American Community Survey, HUD'),
    ('Growth', 'planned', None, 'Population, jobs and new homes, and how each part of the city shares in that growth.', 'Census, Bureau of Labor Statistics, DC permits'),
    ('Land use', 'planned', None, 'How land is zoned and used, how many homes the rules allow, and what actually gets permitted and built.', 'DC zoning maps, building permits'),
    ('Fiscal health', 'planned', None, 'Revenue, spending and reserves, and what residents get for each budget dollar.', 'DC Chief Financial Officer'),
    ('Resident satisfaction', 'future', None, 'What residents say about their neighborhoods and city services, from a recurring survey.', 'A survey still to be designed'),
]
rows = ['<div class="rc-row rc-cols" aria-hidden="true"><span>Subject</span><span>What it grades</span><span>Data</span><span style="justify-self:end">DC grade</span></div>']
for name, st, href, what, src in CATS:
    tag = {'live': '<span class="tag live">Live</span>', 'planned': '<span class="tag">Planned</span>', 'future': '<span class="tag">Future</span>'}[st]
    if st == 'live':
        grade = f'<span class="rc-grade"><span class="rc-letter">{city["grade"]}</span><span class="rc-letter-sub">vs similar-size cities</span></span>'
        subj = f'<span class="rc-subj"><b>{name}</b>{tag}<span class="rc-open">Open the scorecard</span></span>'
    else:
        grade = '<span class="rc-grade"><span class="rc-none">Not yet graded</span></span>'
        subj = f'<span class="rc-subj"><b>{name}</b>{tag}</span>'
    inner = f'{subj}<span class="rc-what">{what}</span><span class="rc-src">{src}</span>{grade}'
    rows.append(f'<a class="rc-row" href="{href}">{inner}</a>' if href else f'<div class="rc-row">{inner}</div>')

home = f'''<section class="hero">
  <div>
    <h1>How is DC doing, block by block?</h1>
    <p>A report card for the District and every one of its 8 wards, 46 Advisory Neighborhood Commissions and 345 single-member districts, built from the city's own public data. Each grade shows where an area stands and which way it is heading.</p>
    <form class="find" action="traffic-safety/" method="get">
      <label for="q">Look up your neighborhood</label>
      <input id="q" name="q" type="search" placeholder="Ward 4, 4D or 4D02" autocomplete="off" required>
      <button type="submit">Show grade</button>
      <small>Don't know your ANC? Find it on the <a href="https://anc.dc.gov/">Office of ANCs site</a>.</small>
    </form>
  </div>
  {hero_map}
</section>

<div class="rc-head">
  <h2>The report card</h2>
  <p>One scorecard is live. The others are next.</p>
</div>
<div class="report">{''.join(rows)}</div>

<section class="explain">
  <div><h3>How grades work</h3><p>Each area gets a letter, A to F, for how it compares with DC as a whole, and a plus or minus when it is improving or worsening faster than the city. Cutoffs are fixed, so every area can earn an A. DC itself is graded against US cities of similar size.</p></div>
  <div><h3>Built on public data</h3><p>Every number comes from DC Open Data and other public sources. Each scorecard explains its measures, sources and limits, and the code that builds the numbers is published with the site.</p></div>
  <div><h3>Independent</h3><p>{SITE} is a volunteer project. It is nonpartisan, does not endorse candidates, and is not affiliated with the DC government.</p></div>
</section>'''
open(S + '/index.html', 'w').write(shell(f'{SITE}: a report card for DC, block by block', f'{SITE} grades DC and each ward, ANC and single-member district on traffic safety and more, using public data.', home, '/', root=''))

# ---------- about ----------
about = f'''<div class="prose">
  <h1>About {SITE}</h1>
  <p>{SITE} turns DC's public data into plain report cards for the whole city and for every ward, Advisory Neighborhood Commission (ANC) and single-member district. It shows residents, commissioners and policymakers where things are working, where they are not, and which way they are heading.</p>
  <h2>Principles</h2>
  <ul>
    <li><b>Outcomes over activity.</b> Grades measure results residents feel, like people hurt in crashes, not how much was spent or how many programs exist.</li>
    <li><b>Fair comparisons.</b> Areas are compared per resident and, where it matters, per vehicle mile or per household, so large and small areas are judged on the same terms.</li>
    <li><b>Direction matters.</b> Every grade carries a plus or minus for whether an area is improving or worsening compared with the city as a whole.</li>
    <li><b>Show the work.</b> Each scorecard explains its measures, sources and limits, and the code is public.</li>
    <li><b>Independent and nonpartisan.</b> {SITE} does not endorse candidates or parties and is not affiliated with the DC government.</li>
  </ul>
  <h2>Data</h2>
  <p>Scorecards use DC Open Data (opendata.dc.gov) and other public sources named on each page. Numbers are refreshed as new data is released, and each page shows how current it is.</p>
  <h2>Contact</h2>
  <p>Questions, corrections or ideas for new measures: add your contact email here.</p>
</div>'''
open(S + '/about/index.html', 'w').write(shell(f'About | {SITE}', f'What {SITE} is, how it grades DC, and where the data comes from.', about, '/about/', root='../'))
open(S + '/404.html', 'w').write(shell(f'Page not found | {SITE}', 'Page not found', '<div class="prose"><h1>Page not found</h1><p>That page does not exist. <a href="/">Go to the home page</a>.</p></div>', '', root='/'))
open(S + '/.nojekyll', 'w').write('')
print('site built', sum(len(fs) for _, _, fs in os.walk(S)), 'files')
