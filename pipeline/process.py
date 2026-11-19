import csv, json, math, sys, collections, datetime
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
from shapely.ops import unary_union

CSV, GEO, OUT, TRAFFIC = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
FC = sys.argv[5] if len(sys.argv) > 5 else None
# freeways (FHWA class 1 Interstate, 2 Other Freeway and Expressway) are left out of the per-vehicle-mile measure
FWB = []
if FC:
    for f in json.load(open(FC))['features']:
        p = f['properties']
        if p['FHWAFUNCTIONALCLASS'] in (1, 2) and f['geometry']:
            FWB.append((p['ROUTEID'], shape(f['geometry'])))
FWR = {r for r, _ in FWB}
FWTREE = STRtree([g for _, g in FWB]) if FWB else None
def on_freeway(route, pt, d):
    if route not in FWR: return False
    return any(FWB[j][0] == route for j in FWTREE.query(pt, predicate='dwithin', distance=d))
print('freeway blocks', len(FWB), 'routes', len(FWR))
tf = json.load(open(TRAFFIC))['features']
gk = collections.Counter(json.dumps(f['geometry']['coordinates']) for f in tf if f['geometry'])
segs = [f for f in tf if f['geometry'] and gk[json.dumps(f['geometry']['coordinates'])] == 1]
from shapely.geometry import LineString
ROUTES = set(f['properties']['ROUTEID'] for f in segs)
SEGTREE = STRtree([LineString([c[:2] for c in f['geometry']['coordinates']]) for f in segs])
print('traffic segments kept', len(segs), 'of', len(tf))
g = json.load(open(GEO))
smds = []
for f in g['features']:
    p = f['properties']
    smds.append(dict(id=p['SMD_ID'], anc=p['ANC_ID'], rep=(p.get('REP_NAME') or '').title().strip(),
                     geom=shape(f['geometry']).buffer(0)))
tree = STRtree([s['geom'] for s in smds])

LAT0 = math.radians(38.9)
def owners(pt):
    ids = [smds[j]['id'] for j in tree.query(pt, predicate='dwithin', distance=0.0002)]
    if not ids:
        j = tree.nearest(pt)
        if smds[j]['geom'].distance(pt) < 0.0006: ids = [smds[j]['id']]
    return ids
def sqmi(geom):
    return geom.area * 69.172 * math.cos(LAT0) * 68.99

YEARS = list(range(2016, 2027))  # 2016 on: earlier years code serious injuries differently and are incomplete
def blank():
    return {k: {y: 0 for y in YEARS} for k in ('crashes','ksi','fatal','ped','bike','speed','crashes_c','ksi_c','ped_c','bike_c','fatal_c','crashes_on')}
agg = {s['id']: blank() for s in smds}
unmatched = 0; used = 0; maxdate = None
fw_crashes = collections.Counter()
ytd_rows = []  # (smd, date, metrics) for YTD calc

def I(row, k):
    v = row.get(k) or '0'
    try: return int(float(v))
    except: return 0

with open(CSV, encoding='utf-8-sig') as fh:
    for row in csv.DictReader(fh):
        d = row['REPORTDATE'][:10].replace('/','-')
        if len(d) < 10: continue
        y = int(d[:4])
        if y not in YEARS: continue
        try:
            lat, lon = float(row['LATITUDE']), float(row['LONGITUDE'])
        except: continue
        if not (38.78 < lat < 39.0 and -77.13 < lon < -76.9): unmatched += 1; continue
        pt = Point(lon, lat)
        hit = None
        for i in tree.query(pt):
            if smds[i]['geom'].covers(pt): hit = smds[i]['id']; break
        if hit is None:
            # snap to nearest SMD if within ~50 m (crashes on boundary streets)
            i = tree.nearest(pt)
            if smds[i]['geom'].distance(pt) < 0.0006: hit = smds[i]['id']
        if hit is None: unmatched += 1; continue
        used += 1
        dt = datetime.date.fromisoformat(d)
        if maxdate is None or dt > maxdate: maxdate = dt
        maj = sum(I(row,k) for k in ('MAJORINJURIES_BICYCLIST','MAJORINJURIES_DRIVER','MAJORINJURIES_PEDESTRIAN','MAJORINJURIESPASSENGER','MAJORINJURIESOTHER'))
        fat = sum(I(row,k) for k in ('FATAL_BICYCLIST','FATAL_DRIVER','FATAL_PEDESTRIAN','FATALPASSENGER','FATALOTHER'))
        ped = sum(I(row,k) for k in ('MAJORINJURIES_PEDESTRIAN','MINORINJURIES_PEDESTRIAN','FATAL_PEDESTRIAN'))
        bike = sum(I(row,k) for k in ('MAJORINJURIES_BICYCLIST','MINORINJURIES_BICYCLIST','FATAL_BICYCLIST'))
        spd = 1 if I(row,'SPEEDING_INVOLVED') > 0 else 0
        # a crash within about 20 yards of a district line (usually a border street) is split evenly between the
        # districts on each side, in every measure, so the same crash counts the same way everywhere
        own = owners(pt) or [hit]; w = 1 / len(own)
        on_counted = False
        if on_freeway(row['ROUTEID'], pt, 0.0005):
            fw_crashes[y] += 1
        elif row['ROUTEID'] in ROUTES or len(SEGTREE.query(pt, predicate='dwithin', distance=0.0003)):
            on_counted = True
        for o in own:
            a = agg[o]
            a['crashes'][y] += w; a['ksi'][y] += (maj + fat) * w; a['fatal'][y] += fat * w
            a['ped'][y] += ped * w; a['bike'][y] += bike * w; a['speed'][y] += spd * w
            if on_counted:
                a['crashes_on'][y] += w
                a['crashes_c'][y] += w; a['ksi_c'][y] += (maj + fat) * w; a['ped_c'][y] += ped * w; a['bike_c'][y] += bike * w; a['fatal_c'][y] += fat * w
            if y in (2025, 2026): ytd_rows.append((o, dt, w, (maj + fat) * w, ped * w, bike * w))

# annual vehicle miles on counted roads, by district (pieces of each segment assigned by midpoint)
vmt = collections.Counter()
fw_vmt = 0.0; road_mi = 0.0
KX = math.cos(LAT0) * 69.172
for f in segs:
    cs = f['geometry']['coordinates']; aadt = f['properties']['AADT']; rt = f['properties']['ROUTEID']
    for (x1, y1, *_), (x2, y2, *_) in zip(cs, cs[1:]):
        L = math.hypot((x2 - x1) * KX, (y2 - y1) * 68.99)
        if L == 0: continue
        n = max(1, math.ceil(L / 0.01))
        for i in range(n):
            t = (i + 0.5) / n; pt = Point(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
            if on_freeway(rt, pt, 0.0003): fw_vmt += aadt * (L / n) * 365; continue
            road_mi += L / n
            own = owners(pt)
            for o in own: vmt[o] += aadt * (L / n) * 365 / len(own)
print('annual VMT (billions) non-freeway', round(sum(vmt.values()) / 1e9, 3), 'freeway', round(fw_vmt / 1e9, 3), 'road miles', round(road_mi), 'freeway crashes', dict(fw_crashes))

# YTD comparison: Jan 1 - maxdate (month/day) in 2026 vs same window 2025
cut25 = maxdate.replace(year=2025)
ytd = collections.defaultdict(lambda: {'c26':0,'c25':0,'k26':0,'k25':0})
for sid, dt, c, k, p, b in ytd_rows:
    if dt.year == 2026: ytd[sid]['c26'] += c; ytd[sid]['k26'] += k
    elif dt <= cut25: ytd[sid]['c25'] += c; ytd[sid]['k25'] += k

BASE = (2023, 2024, 2025)
def summarize(a, area):
    out = {'area': round(area, 3)}
    for k in a:
        out[k + '_yr'] = {str(y): a[k][y] for y in YEARS}
        avg = sum(a[k][y] for y in BASE) / 3
        out[k] = round(avg, 1)
        out[k + '_sqmi'] = round(avg / area, 1) if area else None
    return out

smd_out = {}
for s in smds:
    o = summarize(agg[s['id']], sqmi(s['geom']))
    o.update(anc=s['anc'], rep=s['rep'], ytd=ytd[s['id']], vmt=vmt[s['id']])
    smd_out[s['id']] = o

anc_ids = sorted({s['anc'] for s in smds})
anc_out = {}
for aid in anc_ids:
    members = [s for s in smds if s['anc'] == aid]
    tot = blank()
    for s in members:
        for k in tot:
            for y in YEARS: tot[k][y] += agg[s['id']][k][y]
    area = sum(sqmi(s['geom']) for s in members)
    o = summarize(tot, area)
    yy = {'c26':0,'c25':0,'k26':0,'k25':0}
    for s in members:
        for k in yy: yy[k] += ytd[s['id']][k]
    o.update(smds=sorted(s['id'] for s in members), ytd=yy, vmt=sum(vmt[s['id']] for s in members))
    anc_out[aid] = o

# ranks (1 = highest value = most crashes)
METRICS = ['crashes','ksi','ped','bike','fatal','speed']
for table in (smd_out, anc_out):
    for m in METRICS:
        for suf in ('', '_sqmi'):
            key = m + suf
            order = sorted(table, key=lambda i: -(table[i][key] or 0))
            for r, i in enumerate(order, 1):
                table[i].setdefault('rank', {})[key] = r

# geometry: simplified SMDs + dissolved ANCs
def rnd(geom, tol):
    g2 = geom.simplify(tol, preserve_topology=True)
    gj = mapping(g2)
    def r(c):
        if isinstance(c[0], (float, int)): return [round(c[0], 5), round(c[1], 5)]
        return [r(x) for x in c]
    return {'type': gj['type'], 'coordinates': r(gj['coordinates'])}
smd_feats = [{'type':'Feature','properties':{'id':s['id'],'anc':s['anc']},'geometry':rnd(s['geom'],0.00008)} for s in smds]
anc_feats = []
for aid in anc_ids:
    u = unary_union([s['geom'] for s in smds if s['anc']==aid]).buffer(0)
    anc_feats.append({'type':'Feature','properties':{'id':aid,'ward':aid[0] if aid[0].isdigit() else aid},'geometry':rnd(u,0.0001)})

city = {k: round(sum(smd_out[i][k] for i in smd_out),1) for k in METRICS}
meta = dict(maxdate=maxdate.isoformat(), used=used, unmatched=unmatched, base='2023-2025', years=YEARS, city=city,
            road_miles=round(road_mi), freeway_vmt=fw_vmt, freeway_crashes=round(sum(fw_crashes[y] for y in BASE) / 3))
json.dump(dict(meta=meta, smd=smd_out, anc=anc_out,
               geo={'smd':{'type':'FeatureCollection','features':smd_feats},
                    'anc':{'type':'FeatureCollection','features':anc_feats}}),
          open(OUT,'w'), separators=(',',':'))
print(json.dumps(meta, indent=1))
print('4D', {k: anc_out['4D'][k] for k in ['crashes','ksi','ped','bike','fatal','area']}, anc_out['4D']['rank']['crashes'], anc_out['4D']['ytd'])
print('4D02', {k: smd_out['4D02'][k] for k in ['crashes','ksi','ped','bike','fatal','area']}, smd_out['4D02']['rank']['crashes'], smd_out['4D02']['rep'])
