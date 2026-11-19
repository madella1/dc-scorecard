"""Draft grades. usage: grade.py OUTDIR"""
import csv, json, math, sys, collections
OUT = sys.argv[1]
rd = lambda f: list(csv.DictReader(open(f'{OUT}/{f}')))
smd, anc, ward = rd('dc-crashes-by-smd.csv'), rd('dc-crashes-by-anc.csv'), rd('dc-crashes-by-ward.csv')
city = rd('dc-crashes-city.csv')[0]
tr = json.load(open(f'{OUT}/trend.json'))
F = lambda r, k: float(r[k]) if r.get(k) not in (None, '') else None
N = lambda r: float(r.get('smd_count') or 1)

DC_N = 345
mu = {'ksi': F(city, 'ksi') / DC_N, 'vru': (F(city, 'ped') + F(city, 'bike')) / DC_N, 'vmt': F(city, 'crashes_per_100m_vmt')}

def obs(r):
    """3-year counts and exposures for the three standing measures"""
    o = {'ksi': (F(r, 'ksi') * 3, N(r) * 3), 'vru': ((F(r, 'ped') + F(r, 'bike')) * 3, N(r) * 3)}
    rate, vm = F(r, 'crashes_per_100m_vmt'), F(r, 'vehicle_miles_millions')
    if rate is not None and vm:
        e = vm / 100 * 3; o['vmt'] = (rate * e, e)
    return o

# prior strength per measure from SMD spread (method of moments, Poisson-gamma)
A = {}
for m in mu:
    pairs = [obs(r)[m] for r in smd if m in obs(r)]
    rates = [o / e for o, e in pairs]; E = [e for _, e in pairs]
    mean = sum(o for o, _ in pairs) / sum(E)
    var = sum((x - mean) ** 2 for x in rates) / len(rates)
    tau2 = max(var - mean / (sum(E) / len(E)), 1e-9)
    A[m] = max(3.0, mean ** 2 / tau2)
print('prior strength (cases)', {k: round(v, 1) for k, v in A.items()})

W = {'ksi': 0.4, 'vru': 0.4, 'vmt': 0.2}
def standing(r, vmt_mu):
    mu['vmt'] = vmt_mu
    o = obs(r); num = den = 0; parts = {}
    for m, (O, E) in o.items():
        shr = (O + A[m]) / (E + A[m] / mu[m])
        parts[m] = shr / mu[m]
        num += W[m] * math.log2(parts[m]); den += W[m]
    return 2 ** (num / den), parts

g_c = sum(v['c2'] for v in tr.values()) / sum(v['c1'] for v in tr.values())
g_h = sum(v['h2'] for v in tr.values()) / sum(v['h1'] for v in tr.values())
K = 15
def trend(ids):
    c1 = sum(tr.get(i, {}).get('c1', 0) for i in ids); c2 = sum(tr.get(i, {}).get('c2', 0) for i in ids)
    h1 = sum(tr.get(i, {}).get('h1', 0) for i in ids); h2 = sum(tr.get(i, {}).get('h2', 0) for i in ids)
    rc = (c2 + K) / (c1 * g_c + K); rh = (h2 + K) / (h1 * g_h + K)
    return 2 ** (0.5 * math.log2(rc) + 0.5 * math.log2(rh)), (c1, c2, h1, h2)

CUT = [(0.5, 'A'), (0.8, 'B'), (1.25, 'C'), (2.0, 'D'), (99, 'F')]
def letter(s, t):
    L = next(l for c, l in CUT if s <= c)
    sign = '+' if t <= 0.88 else ('-' if t >= 1.12 else '')
    return L, sign

smd_by_anc = collections.defaultdict(list); smd_by_ward = collections.defaultdict(list)
for r in smd: smd_by_anc[r['anc']].append(r['smd']); smd_by_ward[r['ward']].append(r['smd'])

import statistics
VM = {l: statistics.median(F(r,'crashes_per_100m_vmt') for r in rows if F(r,'crashes_per_100m_vmt') is not None) for l, rows in (('smd',smd),('anc',anc),('ward',ward))}
print('typical vmt rate', VM)
res = {}
for lvl, rows, key, ids in (('smd', smd, 'smd', lambda r: [r['smd']]), ('anc', anc, 'anc', lambda r: smd_by_anc[r['anc']]),
                            ('ward', ward, 'ward', lambda r: smd_by_ward[r['ward']])):
    out = []
    for r in rows:
        s, parts = standing(r, VM[lvl]); t, cnts = trend(ids(r)); L, sg = letter(s, t)
        out.append(dict(id=r[key], standing=round(s, 2), parts={k: round(v, 2) for k, v in parts.items()}, trend=round(t, 2),
                        counts=cnts, letter=L, sign=sg, grade=L + sg))
    res[lvl] = out
    dist = collections.Counter(o['letter'] for o in out); sd = collections.Counter(o['sign'] or '=' for o in out)
    print(lvl, 'letters', dict(sorted(dist.items())), 'trend', dict(sd))
json.dump(res, open(f'{OUT}/grades_draft.json', 'w'), indent=1)

# ---- write grade columns into the level CSVs ----
ORDER = 'ABCDF'
def cols_for(o):
    p = o['parts']; c1, c2, h1, h2 = o['counts']
    return {'grade': o['grade'], 'grade_letter': o['letter'], 'grade_sign': o['sign'],
            'grade_sort': ORDER.index(o['letter']) * 3 + {'+': 0, '': 1, '-': 2}[o['sign']],
            'harm_vs_dc': o['standing'], 'ksi_vs_dc': p['ksi'], 'vru_vs_dc': p['vru'], 'vmt_vs_typical': p.get('vmt', ''),
            'trend_vs_dc_pct': round((o['trend'] - 1) * 100), 'crashes_prev_2y': c1, 'crashes_last_2y': c2, 'hurt_prev_2y': h1, 'hurt_last_2y': h2}
GCOLS = list(cols_for(res['smd'][0]).keys())
for lvl, fn, key in (('smd', 'dc-crashes-by-smd.csv', 'smd'), ('anc', 'dc-crashes-by-anc.csv', 'anc'), ('ward', 'dc-crashes-by-ward.csv', 'ward')):
    rows = rd(fn); g = {o['id']: cols_for(o) for o in res[lvl]}
    head = [c for c in rows[0].keys() if c not in GCOLS]
    head = head[:1] + GCOLS[:2] + head[1:] + GCOLS[2:]
    with open(f'{OUT}/{fn}', 'w', newline='') as fh:
        w = csv.DictWriter(fh, head); w.writeheader()
        for r in rows: r.update(g[r[key]]); w.writerow({k: r.get(k, '') for k in head})

# ---- city: traffic deaths per 100,000 residents vs US cities of 500,000 to 1 million (3-year windows, from peers.py: NHTSA FARS + Census) ----
import statistics
PS = json.load(open(f'{OUT}/peer_summary.json'))
c_stand, c_trend = PS['standing'], PS['trend']
cl, cs = letter(c_stand, c_trend)
crow = rd('dc-crashes-city.csv')[0]
tc = {k: sum(v[k] for v in tr.values()) for k in ('c1', 'c2', 'h1', 'h2')}
crow.update({'grade': cl + cs, 'grade_letter': cl, 'grade_sign': cs, 'grade_sort': ORDER.index(cl) * 3 + {'+': 0, '': 1, '-': 2}[cs],
             'peer_deaths_per_100k': PS['dc_rate'], 'peer_deaths_per_100k_before': PS['dc_prior'], 'peer_median_deaths_per_100k': PS['median'], 'peer_rank': PS['dc_rank'], 'peer_count': PS['count'],
             'peer_change_pct': PS['dc_change_pct'], 'peer_median_change_pct': PS['median_change_pct'], 'harm_vs_peers': round(c_stand, 2),
             'peer_period': PS['period'].replace('-', ' to '), 'peer_prior_period': PS['prior_period'].replace('-', ' to '),
             'crashes_prev_2y': tc['c1'], 'crashes_last_2y': tc['c2'], 'hurt_prev_2y': tc['h1'], 'hurt_last_2y': tc['h2'],
             'crashes_2y_change_pct': round((g_c - 1) * 100), 'hurt_2y_change_pct': round((g_h - 1) * 100)})
head = list(dict.fromkeys(['city', 'grade'] + list(crow.keys())))
with open(f'{OUT}/dc-crashes-city.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, head); w.writeheader(); w.writerow(crow)
print('CITY', cl + cs, PS)
