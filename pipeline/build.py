import json, math, csv, sys
def rd2(v):
    v = round(v, 2)  # crashes on district lines are split, so counts can be fractions
    return int(v) if v == int(v) else v
from shapely.geometry import shape
from shapely.ops import unary_union, transform
S = sys.argv[1]; GEO = sys.argv[2]
d = json.load(open(S + '/out/data.json'))
meta, smd, anc = d['meta'], d['smd'], d['anc']
g = json.load(open(GEO))
geoms = {f['properties']['SMD_ID']: shape(f['geometry']).buffer(0) for f in g['features']}
allg = unary_union(list(geoms.values()))
LAT0 = 38.9; KX = math.cos(math.radians(LAT0))
minx, miny, maxx, maxy = allg.bounds
W = 1000.0; sc = W / ((maxx - minx) * KX)
H = (maxy - miny) * sc
proj = lambda x, y, z=None: ((x - minx) * KX * sc, (maxy - y) * sc)
def path(geom, tol):
    p = transform(proj, geom).simplify(tol, preserve_topology=True)
    polys = [p] if p.geom_type == 'Polygon' else list(p.geoms)
    out = []
    for poly in polys:
        for ring in [poly.exterior] + list(poly.interiors):
            cs = list(ring.coords)[:-1]
            if len(cs) < 3: continue
            out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in cs) + 'Z')
    return ''.join(out)
rows = []
for sid, gm in geoms.items():
    rp = transform(proj, gm).representative_point()
    rows.append({'level': 'smd', 'id': sid, 'anc': smd[sid]['anc'], 'path': path(gm, 0.35), 'lx': round(rp.x, 1), 'ly': round(rp.y, 1), 'map_w': W, 'map_h': round(H, 1)})
for aid in sorted(anc):
    u = unary_union([geoms[s] for s in anc[aid]['smds']]).buffer(0)
    rp = transform(proj, u).representative_point()
    rows.append({'level': 'anc', 'id': aid, 'anc': aid, 'path': path(u, 0.5), 'lx': round(rp.x, 1), 'ly': round(rp.y, 1), 'map_w': W, 'map_h': round(H, 1)})
WARD = json.load(open(S + '/out/smd_ward.json'))
for w in sorted(set(WARD.values())):
    u = unary_union([geoms[s] for s in geoms if WARD[s] == w]).buffer(0)
    rp = transform(proj, u).representative_point()
    rows.append({'level': 'ward', 'id': w, 'anc': '', 'path': path(u, 0.6), 'lx': round(rp.x, 1), 'ly': round(rp.y, 1), 'map_w': W, 'map_h': round(H, 1)})
rp = transform(proj, allg).representative_point()
rows.append({'level': 'city', 'id': 'DC', 'anc': '', 'path': path(allg.buffer(0), 0.6), 'lx': round(rp.x, 1), 'ly': round(rp.y, 1), 'map_w': W, 'map_h': round(H, 1)})
json.dump(rows, open(S + '/out/dc-district-outlines.json', 'w'), separators=(',', ':'))
# major road overlay: Interstate (1), Other Freeway and Expressway (2), Principal Arterial (3), merged by class and street name
FC = sys.argv[3] if len(sys.argv) > 3 else None
if FC:
    from shapely.ops import linemerge
    from collections import defaultdict
    grp = defaultdict(list)
    for f in json.load(open(FC))['features']:
        p = f['properties']; c = p['FHWAFUNCTIONALCLASS']
        if c in (1, 2, 3) and f['geometry']:
            import re
            nm = re.sub(r'\s+(BN|I)(?=\s|$)', '', ' '.join((p['ROUTENAME'] or '').split())).strip()
            parts = nm.split(); quad = parts[-1] if parts and parts[-1] in ('NW', 'NE', 'SW', 'SE') else None
            nm = ' '.join(parts[:-1] if quad else parts).title()
            nm = re.sub(r'(\d)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), nm).replace(' Brg', ' Bridge').replace(' Expy', ' Expressway').replace(' Fwy', ' Freeway').replace(' Pkwy', ' Parkway').replace('G W ', 'George Washington ')
            nm = nm + (' ' + quad if quad else '')
            grp[(c, nm)].append(shape(f['geometry']))
    CLS = {1: 'Interstate', 2: 'Other freeway and expressway', 3: 'Principal arterial'}
    roads = []
    for (c, nm), gs in sorted(grp.items()):
        u = unary_union(gs)
        if u.geom_type == 'MultiLineString': u = linemerge(u)
        m = transform(proj, u).simplify(0.4)
        lines = [m] if m.geom_type == 'LineString' else list(m.geoms)
        d = ''.join('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in ln.coords) for ln in lines if len(ln.coords) > 1)
        if d: roads.append({'class': CLS[c], 'class_code': c, 'name': nm, 'path': d})
    json.dump(roads, open(S + '/out/dc-major-roads.json', 'w'), separators=(',', ':'))
    print('roads', len(roads), 'bytes', len(json.dumps(roads)))
print('outlines', len(rows), 'H', round(H, 1))

YEARS = [str(y) for y in meta['years']]
MET = ['crashes', 'ksi', 'ped', 'bike']
def rnd(m, v):
    return int(round(v)) if m == 'crashes' else round(v, 1)
def pct(a, b):
    return '' if b == 0 else round((a - b) / b * 100)
VMT_MIN = 2e6  # annual vehicle miles on counted roads needed before a traffic rate is shown
SUFFIX = ['', '_per_district', '_per_sqmi', '_per_100m_vmt']
def val(m, v, suf):
    if v is None: return ''
    if m == 'crashes' and suf != '_per_district': return int(round(v))
    return round(v, 1)
def row(rec, key, keyval, extra, ndist):
    r = {key: keyval}; r.update(extra)
    r['area_sqmi'] = round(rec['area'], 3)
    r['vehicle_miles_millions'] = round(rec['vmt'] / 1e6, 1)
    base_c = sum(rec['crashes_yr'][str(y)] for y in BASE); cnt_c = sum(rec['crashes_on_yr'][str(y)] for y in BASE)
    r['counted_road_share_pct'] = int(round(cnt_c / base_c * 100)) if base_c else ''
    for m in MET:
        avg = rec[m]; avg_c = sum(rec[m + '_c_yr'][str(y)] for y in BASE) / 3
        r[m] = val(m, avg, '')
        r[m + '_per_district'] = val(m, avg / ndist, '_per_district')
        r[m + '_per_sqmi'] = val(m, avg / rec['area'], '_per_sqmi')
        r[m + '_per_100m_vmt'] = val(m, avg_c / (rec['vmt'] / 1e8), '_per_100m_vmt') if rec['vmt'] >= VMT_MIN else ''
    for m in MET:
        for y in YEARS:
            r[f'{m}_{y}'] = rd2(rec[m + '_yr'][y])
    for m in MET:  # counted-street crashes by year (boundary roads split), for per-vehicle-mile rates in any window
        for y in YEARS:
            r[f'{m}_c_{y}'] = round(rec[m + '_c_yr'][y], 2)
    yt = rec['ytd']
    r['crashes_2026_ytd'] = rd2(yt['c26']); r['crashes_2025_same_period'] = rd2(yt['c25']); r['crashes_ytd_change_pct'] = pct(yt['c26'], yt['c25'])
    r['ksi_2026_ytd'] = rd2(yt['k26']); r['ksi_2025_same_period'] = rd2(yt['k25'])
    return r
BASE = (2023, 2024, 2025)
def add_ranks(rows):
    for m in MET:
        for suf in SUFFIX:
            f = m + suf
            have = [r for r in rows if r[f] != '']
            for i, r in enumerate(sorted(have, key=lambda r: -r[f]), 1): r[f + '_rank'] = i
            for r in rows:
                r.setdefault(f + '_rank', '')
anc_rows = [row(anc[a], 'anc', a, {'ward': a[:-1], 'smd_count': len(anc[a]['smds'])}, len(anc[a]['smds'])) for a in sorted(anc)]
smd_rows = [row(smd[s], 'smd', s, {'anc': smd[s]['anc'], 'ward': WARD[s], 'commissioner': smd[s]['rep']}, 1) for s in sorted(smd)]
def aggr(ids):
    recs = [smd[i] for i in ids]
    out = {'area': sum(r['area'] for r in recs), 'vmt': sum(r['vmt'] for r in recs), 'ytd': {k: sum(r['ytd'][k] for r in recs) for k in recs[0]['ytd']}}
    for k in recs[0]:
        if k.endswith('_yr'): out[k] = {y: sum(r[k][y] for r in recs) for y in recs[0][k]}
    for k in [k for k in out if k.endswith('_yr')]:
        out[k[:-3]] = sum(out[k][str(y)] for y in BASE) / 3
    return out
ward_ids = {}
for sid, w in WARD.items(): ward_ids.setdefault(w, []).append(sid)
ward_rows = [row(aggr(ids), 'ward', w, {'smd_count': len(ids), 'anc_count': len({smd[i]['anc'] for i in ids})}, len(ids)) for w, ids in sorted(ward_ids.items())]
city_rows = [row(aggr(list(smd)), 'city', 'DC', {'smd_count': len(smd), 'anc_count': len(anc), 'ward_count': len(ward_ids)}, len(smd))]
add_ranks(anc_rows); add_ranks(smd_rows); add_ranks(ward_rows)
# traffic deaths: shown only for wards and the city, where there are enough to compare.
# The comparison measures use the 2019-2025 yearly average (seven full years), since three years is too few deaths.
FULL = [str(y) for y in range(2019, 2026)]
def add_deaths(r, rec, ndist):
    r['deaths'] = round(rec['fatal'], 1)
    for y in YEARS: r[f'deaths_{y}'] = rd2(rec['fatal_yr'][y])
    for y in YEARS: r[f'deaths_c_{y}'] = round(rec['fatal_c_yr'][y], 2)
    r['deaths_since_2019'] = rd2(sum(rec['fatal_yr'][y] for y in YEARS if int(y) >= 2019))  # tiles and averages stay on 2019 on
    avg = sum(rec['fatal_yr'][y] for y in FULL) / len(FULL); avg_c = sum(rec['fatal_c_yr'][y] for y in FULL) / len(FULL)
    r['deaths_avg'] = round(avg, 2)
    r['deaths_avg_per_district'] = round(avg / ndist, 3)
    r['deaths_avg_per_sqmi'] = round(avg / rec['area'], 3)
    r['deaths_avg_per_100m_vmt'] = round(avg_c / (rec['vmt'] / 1e8), 2) if rec['vmt'] >= VMT_MIN else ''
for r, (w, ids) in zip(ward_rows, sorted(ward_ids.items())): add_deaths(r, aggr(ids), len(ids))
for f in ('deaths_since_2019', 'deaths_avg', 'deaths_avg_per_district', 'deaths_avg_per_sqmi', 'deaths_avg_per_100m_vmt'):
    for r in ward_rows: r[f + '_rank'] = '' if r[f] == '' else 1 + sum(o[f] != '' and o[f] > r[f] for o in ward_rows)  # ties share a rank
add_deaths(city_rows[0], aggr(list(smd)), len(smd))
print('deaths', [(r['ward'], r['deaths_avg'], r['deaths_avg_per_district'], r['deaths_avg_per_sqmi'], r['deaths_avg_per_100m_vmt'], r['deaths_avg_per_district_rank']) for r in ward_rows], {k: city_rows[0][k] for k in city_rows[0] if k.startswith('deaths_avg')})
for name, rs in (('dc-crashes-by-anc.csv', anc_rows), ('dc-crashes-by-smd.csv', smd_rows), ('dc-crashes-by-ward.csv', ward_rows), ('dc-crashes-city.csv', city_rows)):
    with open(S + '/out/' + name, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
city = {'area': None}
tot = {m: sum(r[m] for r in anc_rows) for m in MET}
cityrow = {'scope': 'DC', 'crashes': int(round(sum(anc[a]['crashes'] for a in anc))),
           'ksi': round(sum(anc[a]['ksi'] for a in anc), 1), 'ped': round(sum(anc[a]['ped'] for a in anc), 1),
           'bike': round(sum(anc[a]['bike'] for a in anc), 1), 'anc_count': len(anc_rows), 'smd_count': len(smd_rows), 'ward_count': len(ward_rows), 'city_count': 1,
           'data_through': meta['maxdate'], 'average_years': '2023-2025', 'crashes_per_100m_vmt': int(round(sum(smd[x]['crashes_c'] for x in smd) / (sum(smd[x]['vmt'] for x in smd) / 1e8))), 'smd_with_traffic_rate': sum(1 for r in smd_rows if r['crashes_per_100m_vmt'] != ''), 'counted_road_share_pct': int(round(sum(sum(smd[x]['crashes_on_yr'][str(y)] for y in BASE) for x in smd) / sum(sum(smd[x]['crashes_yr'][str(y)] for y in BASE) for x in smd) * 100)), 'traffic_road_miles': meta['road_miles'], 'freeway_vehicle_miles_billions': round(meta['freeway_vmt'] / 1e9, 2), 'freeway_crashes': meta['freeway_crashes'], 'vehicle_miles_billions': round(sum(smd[x]['vmt'] for x in smd) / 1e9, 2)}
cityrow.update({k: city_rows[0][k] for k in ('crashes', 'ksi', 'ped', 'bike', 'crashes_per_100m_vmt', 'counted_road_share_pct')})
with open(S + '/out/dc-crashes-citywide.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(cityrow)); w.writeheader(); w.writerow(cityrow)
print(cityrow)
print(sorted({r['anc'] for r in anc_rows}))
print([r for r in anc_rows if r['anc']=='4D'][0])
