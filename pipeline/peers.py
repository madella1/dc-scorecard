"""Peer-city traffic death rates from NHTSA FARS and Census population estimates.
usage: peers.py SCRATCHPAD
Inputs (under SCRATCHPAD):
  fars/FARS{YEAR}NationalCSV.zip   FARS national CSV downloads (static.nhtsa.gov/nhtsa/downloads/FARS/{YEAR}/National/)
  census/SUB-EST2020_ALL.csv       Census city population estimates, 2010-2020
  census/sub-est2025.csv           Census city population estimates, 2020-2025
Deaths are grouped by FARS city code (state + CITY), the way the Findings study did it, and matched to the
Census place of the same name. Rates are deaths per 100,000 residents over 3-year windows.
Outputs: out/dc-peer-cities.csv, out/peer_summary.json; prints a check against Schneider et al. (2018-2022)."""
import csv, io, json, re, statistics, sys, zipfile, collections, glob
SP = sys.argv[1]

# ---------- FARS deaths by city code ----------
deaths = collections.defaultdict(collections.Counter); fname = collections.defaultdict(collections.Counter)
years = []
for path in sorted(glob.glob(f'{SP}/fars/FARS*NationalCSV.zip')):
    y = int(re.search(r'FARS(\d{4})', path).group(1)); years.append(y)
    z = zipfile.ZipFile(path); n = [x for x in z.namelist() if x.lower().endswith('accident.csv')][0]
    b = z.read(n); b = b[3:] if b.startswith(b'\xef\xbb\xbf') else b
    for r in csv.DictReader(io.StringIO(b.decode('latin-1'))):
        if r['CITY'] in ('0', '9997', '9998', '9999'): continue
        k = (r['STATE'].zfill(2), r['CITY']); f = int(r['FATALS'])
        deaths[k][y] += f; fname[k][r.get('CITYNAME', '')] += f
years = sorted(years); LAST = years[-1]

# ---------- Census populations (incorporated places and consolidated-city balances) ----------
pop = collections.defaultdict(dict); pname = {}
for r in csv.DictReader(open(f'{SP}/census/SUB-EST2020_ALL.csv', encoding='latin-1')):
    if r['SUMLEV'] != '162': continue
    k = (r['STATE'], r['PLACE']); pname[k] = (r['NAME'], r['STNAME'])
    for y in range(2010, 2020): pop[k][y] = int(r[f'POPESTIMATE{y}'])
for r in csv.DictReader(open(f'{SP}/census/sub-est2025.csv', encoding='latin-1')):
    if r['SUMLEV'] != '162': continue
    k = (r['STATE'], r['PLACE']); pname[k] = (r['NAME'], r['STNAME'])
    for y in range(2020, 2026): pop[k][y] = int(r[f'POPESTIMATE{y}'])

def norm(s):
    s = s.upper().replace('.', '').replace(',', ' ').strip()
    s = re.sub(r'\b(FT)\b', 'FORT', s); s = re.sub(r'\b(ST)\b', 'SAINT', s)
    return re.sub(r'\s+', ' ', s).strip()
def base(census_name):
    s = re.sub(r' \(balance\)$', '', census_name)
    s = re.sub(r' (city|town|village|municipality|urban county|metropolitan government|metro government|unified government|consolidated government)$', '', s)
    s = re.split(r'[-/]', s)[0]  # Nashville-Davidson -> Nashville, Louisville/Jefferson County -> Louisville
    return norm(s)

# FARS code -> Census place, by name within state
by_state = collections.defaultdict(dict)
for k, c in fname.items():
    nm = norm(c.most_common(1)[0][0]); nm = re.sub(r' DC$', '', nm)
    by_state[k[0]].setdefault(nm, k)
big = {k for k, p in pop.items() if max(p.get(y, 0) for y in range(2018, 2026)) >= 400000}
city = {}
for k in big:
    code = by_state[k[0]].get(base(pname[k][0]))
    if code: city[k] = code
missing = sorted(pname[k][0] + ', ' + pname[k][1] for k in big if k not in city)
print('large cities matched', len(city), 'of', len(big), 'unmatched:', missing)

def rate(k, yrs):
    d = sum(deaths[city[k]].get(y, 0) for y in yrs); p = sum(pop[k][y] for y in yrs)
    return d / p * 1e5, d
DC = ('11', '50000')
USPS = dict(zip(['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'],
 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()))

# ---------- check against the published study (2018-2022, Table A1) ----------
STUDY = {'Washington': 4.73, 'Boston': 3.14, 'San Francisco': 3.98, 'Seattle': 4.29, 'Las Vegas': 6.51, 'Baltimore': 7.24, 'Portland': 8.15, 'Denver': 8.78,
         'Columbus': 9.08, 'Mesa': 9.99, 'Austin': 10.27, 'El Paso': 10.49, 'Fresno': 10.96, 'Charlotte': 11.21, 'Sacramento': 11.24, 'Fort Worth': 12.19,
         'Milwaukee': 12.44, 'Oklahoma City': 12.48, 'Indianapolis': 13.92, 'Nashville': 14.53, 'Louisville': 15.73, 'Kansas City': 16.45, 'Jacksonville': 16.68,
         'Albuquerque': 18.60, 'Tucson': 20.05, 'Detroit': 21.40, 'Memphis': 29.60}
STST = {'Portland': 'Oregon', 'Columbus': 'Ohio', 'Kansas City': 'Missouri', 'Washington': 'District of Columbia'}
diffs = []
for c, s in STUDY.items():
    k = next(k for k in city if base(pname[k][0]) == norm(c) and (c not in STST or pname[k][1] == STST[c]))
    r, d = rate(k, range(2018, 2023)); diffs.append(abs(r - s))
print(f'check vs study 2018-2022: mean difference {statistics.mean(diffs):.2f}, largest {max(diffs):.2f} deaths per 100k')

# ---------- current peer comparison: 3-year windows ----------
CUR = list(range(LAST - 2, LAST + 1)); PRI = list(range(LAST - 5, LAST - 2))
peers = [k for k in city if 500000 <= pop[k][LAST] <= 1000000 or k == DC]
rows = []
for k in peers:
    rc, dc = rate(k, CUR); rp, dp = rate(k, PRI)
    nm = base(pname[k][0]).title().replace('Dc', 'DC')
    st = pname[k][1]
    rows.append({'city': 'Washington, DC' if k == DC else f'{nm}, {USPS.get(st, st)}', 'rate': rc, 'prior': rp, 'deaths': dc, 'pop': pop[k][LAST], 'is_dc': int(k == DC)})
others = [r for r in rows if not r['is_dc']]
med = statistics.median(r['rate'] for r in others)
medchg = statistics.median(r['rate'] / r['prior'] for r in others)
rows.sort(key=lambda r: r['rate'])
for i, r in enumerate(rows, 1): r['rank'] = i
dc = next(r for r in rows if r['is_dc'])
summary = {'period': f'{CUR[0]}-{CUR[-1]}', 'prior_period': f'{PRI[0]}-{PRI[-1]}', 'pop_year': LAST, 'count': len(rows),
           'dc_rate': round(dc['rate'], 2), 'dc_prior': round(dc['prior'], 2), 'dc_rank': dc['rank'], 'median': round(med, 2),
           'dc_change_pct': round((dc['rate'] / dc['prior'] - 1) * 100), 'median_change_pct': round((medchg - 1) * 100),
           'standing': round(dc['rate'] / med, 3), 'trend': round((dc['rate'] / dc['prior']) / medchg, 3),
           'check_mean_diff': round(statistics.mean(diffs), 2)}
with open(f'{SP}/out/dc-peer-cities.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['city', 'deaths_per_100k', 'deaths_per_100k_prior', 'change_pct', 'deaths', 'population', 'rank', 'is_dc', 'period', 'prior_period'])
    for r in rows:
        w.writerow([r['city'], round(r['rate'], 2), round(r['prior'], 2), round((r['rate'] / r['prior'] - 1) * 100), r['deaths'], r['pop'], r['rank'], r['is_dc'], summary['period'], summary['prior_period']])
json.dump(summary, open(f'{SP}/out/peer_summary.json', 'w'), indent=1)
# yearly series for the city chart: DC and the typical (median) other peer city.
# Years after the latest FARS file use DC's police crash data as preliminary figures (source = police), with no peer value.
with open(f'{SP}/out/dc-peer-years.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['year', 'dc_deaths', 'dc_per_100k', 'peer_median_per_100k', 'source'])
    pk = [k for k in peers if k != DC]
    for y in years:
        w.writerow([y, deaths[city[DC]].get(y, 0), round(deaths[city[DC]].get(y, 0) / pop[DC][y] * 1e5, 2),
                    round(statistics.median(deaths[city[k]].get(y, 0) / pop[k][y] * 1e5 for k in pk), 2), 'fars'])
    crow = next(csv.DictReader(open(f'{SP}/out/dc-crashes-city.csv')))
    for y in range(LAST + 1, 2100):
        if f'deaths_{y}' not in crow: break
        p = pop[DC].get(y) or pop[DC][max(pop[DC])]  # latest Census estimate for years not yet estimated
        d = int(crow[f'deaths_{y}'])
        w.writerow([y, d, round(d / p * 1e5, 2), '', 'police'])
print(json.dumps(summary, indent=1))
for r in rows: print(f"{r['rank']:2d} {r['city']:32s} {r['rate']:6.2f}  prior {r['prior']:6.2f}  pop {r['pop']:,}")
