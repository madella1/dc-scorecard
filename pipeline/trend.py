"""Count crashes and people hurt per SMD in two 24-month windows ending at the data's last date.
usage: trend.py CSV GEO OUT_JSON"""
import csv, json, sys, datetime, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

CSV, GEO, OUT = sys.argv[1:4]
smds = [dict(id=f['properties']['SMD_ID'], geom=shape(f['geometry']).buffer(0)) for f in json.load(open(GEO))['features']]
tree = STRtree([s['geom'] for s in smds])
def day(row):
    try: return datetime.date.fromisoformat(row['REPORTDATE'][:10].replace('/', '-'))
    except: return None
# windows end at the newest crash date in the file (dates in the future are typos and are ignored)
END = max(d for d in (day(r) for r in csv.DictReader(open(CSV, encoding='utf-8-sig'))) if d and d <= datetime.date.today())
def years_back(d, n):
    try: return d.replace(year=d.year - n)
    except ValueError: return d.replace(year=d.year - n, day=28)
P2 = (years_back(END, 2) + datetime.timedelta(days=1), END)
P1 = (years_back(END, 4) + datetime.timedelta(days=1), years_back(END, 2))
print('recent window', P2, 'earlier window', P1)

def I(row, k):
    try: return int(float(row.get(k) or 0))
    except: return 0

cnt = collections.defaultdict(lambda: {'c1': 0, 'c2': 0, 'h1': 0, 'h2': 0})
with open(CSV, encoding='utf-8-sig') as fh:
    for row in csv.DictReader(fh):
        d = row['REPORTDATE'][:10].replace('/', '-')
        try: dt = datetime.date.fromisoformat(d)
        except: continue
        if dt < P1[0] or dt > END: continue
        try: pt = Point(float(row['LONGITUDE']), float(row['LATITUDE']))
        except: continue
        own = [smds[j]['id'] for j in tree.query(pt, predicate='dwithin', distance=0.0002)]  # border crashes split, as in process.py
        hit = None
        for i in tree.query(pt):
            if smds[i]['geom'].covers(pt): hit = smds[i]['id']; break
        if hit is None:
            i = tree.nearest(pt)
            if smds[i]['geom'].distance(pt) < 0.0006: hit = smds[i]['id']
        if hit is None: continue
        # people hurt: everyone seriously injured or killed, plus pedestrians and cyclists with minor injuries
        ksi = sum(I(row, k) for k in ('MAJORINJURIES_BICYCLIST','MAJORINJURIES_DRIVER','MAJORINJURIES_PEDESTRIAN','MAJORINJURIESPASSENGER','MAJORINJURIESOTHER',
                                      'FATAL_BICYCLIST','FATAL_DRIVER','FATAL_PEDESTRIAN','FATALPASSENGER','FATALOTHER'))
        vru = sum(I(row, k) for k in ('MINORINJURIES_PEDESTRIAN','MINORINJURIES_BICYCLIST'))
        p = '2' if dt >= P2[0] else '1'
        own = own or [hit]
        for o in own:
            cnt[o]['c' + p] += 1 / len(own); cnt[o]['h' + p] += (ksi + vru) / len(own)
json.dump(cnt, open(OUT, 'w'))
t = {k: sum(v[k] for v in cnt.values()) for k in ('c1', 'c2', 'h1', 'h2')}
print(t, 'crash change', round(t['c2'] / t['c1'] - 1, 3), 'hurt change', round(t['h2'] / t['h1'] - 1, 3))
