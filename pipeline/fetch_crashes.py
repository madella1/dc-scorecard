"""Download all of 'Crashes in DC' from DC GIS (MapServer layer 24) into a CSV shaped like the Open Data CSV export.
usage: fetch_crashes.py OUT_CSV"""
import csv, json, ssl, sys, time, urllib.request, urllib.parse, datetime
B = 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Public_Safety_WebMercator/MapServer/24'
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def get(params, tries=8):
    url = B + '/query?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, context=ctx, timeout=120) as r:
                t = r.read().decode()
            if t.startswith('{'):
                d = json.loads(t)
                if 'error' not in d: return d
        except Exception as e:
            pass
        time.sleep(2 + i * 2)
    raise SystemExit('failed: ' + url)
ids = sorted(get({'where': '1=1', 'returnIdsOnly': 'true', 'f': 'json'})['objectIds'])
print('records', len(ids), flush=True)
DATES = {'REPORTDATE', 'FROMDATE', 'TODATE', 'LASTUPDATEDATE'}
def fmt(k, v):
    if v is None: return ''
    if k in DATES: return datetime.datetime.fromtimestamp(v / 1000, datetime.timezone.utc).strftime('%Y/%m/%d %H:%M:%S+00')
    return v
cols = None; n = 0
with open(sys.argv[1], 'w', newline='') as fh:
    w = None
    for i in range(0, len(ids), 1000):
        chunk = ids[i:i + 1000]
        d = get({'where': f'OBJECTID>={chunk[0]} AND OBJECTID<={chunk[-1]}', 'outFields': '*', 'returnGeometry': 'true', 'f': 'json'})
        for f in d['features']:
            a = f['attributes']; g = f.get('geometry') or {}
            row = {'X': g.get('x', ''), 'Y': g.get('y', '')}; row.update({k: fmt(k, v) for k, v in a.items()})
            if w is None:
                cols = list(row.keys()); w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader()
            w.writerow(row); n += 1
        if (i // 1000) % 25 == 0: print(i + len(chunk), n, flush=True)
print('done', n, flush=True)
