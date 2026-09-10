import json, os, base64, datetime, collections, re
S = os.path.dirname(os.path.abspath(__file__))
R = "/Users/michaelweinfeld/Documents/2026/PJ O'Rourke/east-village-178-115"
def J(n):
    p = os.path.join(S, n)
    if not os.path.exists(p) or os.path.getsize(p) < 3: return None
    r = json.load(open(p)); return None if isinstance(r, dict) else r
days = collections.Counter(); d = datetime.date(2026, 6, 1)
while d <= datetime.date(2026, 8, 31): days[(d.weekday() + 1) % 7] += 1; d += datetime.timedelta(days=1)

l_hourly = {dw: [0.0] * 24 for dw in range(7)}
for x in (J('mta_hourly_119.json') or []): l_hourly[int(x['dow'])][int(x['hr'])] = round(float(x['riders']) / days[int(x['dow'])], 1)

def parse_hour(s):
    m = re.search(r'(\d{1,2}):\d{2}:\d{2}\s*(AM|PM)', s, re.I)
    if m: return int(m.group(1)) % 12 + (12 if m.group(2).upper() == 'PM' else 0)
    m = re.search(r'T(\d{2}):', s); return int(m.group(1)) if m else None
door = {'a': ['401686', '401685'], 'b': ['401545', '401555', '401610', '401659']}
bus = {k: {dw: [0.0] * 24 for dw in range(7)} for k in door}
for r in (J('bus_raw.json') or []):
    dt = datetime.date.fromisoformat(r['date'][:10]); dw = (dt.weekday() + 1) % 7; h = parse_hour(r.get('hour', ''))
    if h is None: continue
    for k, ids in door.items():
        if r['stop_id'] in ids: bus[k][dw][h] += float(r.get('boardings') or 0) + float(r.get('alightings') or 0)
for k in bus:
    for dw in bus[k]: bus[k][dw] = [round(v / days[dw], 2) for v in bus[k][dw]]

# monthly at the stops (latest full 12 months average)
mon = collections.defaultdict(lambda: collections.defaultdict(float))
for r in (J('bus_monthly.json') or []):
    for k, ids in door.items():
        if r['stop_id'] in ids: mon[k][r['month'][:7]] += float(r['b']) + float(r['a'])
bus_month = {k: round(sum(v for m, v in sorted(mon[k].items())[-13:-1]) / max(1, len(sorted(mon[k].items())[-13:-1]))) for k in door}

def months_from(hist, daily):
    out = {}
    for r in (J(hist) or []): out[r['month'][:7]] = float(r['riders'])
    for r in (J(daily) or []): out.setdefault(r['day'][:7], 0.0); out[r['day'][:7]] += float(r['riders']) if r['day'][:7] not in {x['month'][:7] for x in (J(hist) or [])} else 0
    return sorted([[m, v] for m, v in out.items() if m <= '2026-08'])
l_months = months_from('mta_hist_119.json', 'mta_daily_119.json')
astor_months = months_from('mta_hist_407.json', 'mta_daily_407.json')

daily = []
w = json.load(open(os.path.join(S, 'weather.json')))['daily']
wx = {t: (w['temperature_2m_max'][i], w['precipitation_sum'][i] or 0.0, w['snowfall_sum'][i] or 0.0) for i, t in enumerate(w['time'])}
for r in (J('mta_daily_119.json') or []):
    dt = r['day'][:10]
    if dt in wx and '2025-01-01' <= dt <= '2026-08-31' and wx[dt][0] is not None:
        t, p, s = wx[dt]; daily.append([dt, round(float(r['riders'])), round(t, 1), round(p, 2), round(s, 2)])

fare = ''
fr = J('fare_119.json')
if fr:
    t = sum(float(x['riders']) for x in fr); top = sorted(fr, key=lambda x: -float(x['riders']))[:4]
    fare = ' · '.join(f"{x['fare_class_category'].replace('OMNY - ','')} {float(x['riders'])/t*100:.0f}%" for x in top) + ' (summer 2026)'

cams = []
for c in (J(os.path.join('ring', 'ring.json')) or []):
    fp = os.path.join(S, c['file'])
    if os.path.exists(fp) and os.path.getsize(fp) > 1000:
        cams.append({'name': c['name'], 'dist': c['dist'], 'id': c['id'], 't': 'Wed 9 Sep 2026, 7:50 pm', 'src': 'data:image/jpeg;base64,' + base64.b64encode(open(fp, 'rb').read()).decode()})

data = {'l_hourly': l_hourly, 'bus_a': bus['a'], 'bus_b': bus['b'], 'bus_month_a': bus_month['a'], 'bus_month_b': bus_month['b'],
        'l_months': l_months, 'astor_months': astor_months, 'daily': daily, 'fare': fare, 'cams': cams}
svg = open(os.path.join(S, 'map.svg')).read()
out = open(os.path.join(S, 'ev_template.html')).read().replace('__MAP__', svg).replace('__DATA__', json.dumps(data, separators=(',', ':')))
open(os.path.join(S, 'index.html'), 'w').write(out)
if os.path.isdir(R): open(os.path.join(R, 'numbers.html'), 'w').write(out)
print(f"built: l_months={len(l_months)} astor={len(astor_months)} daily={len(daily)} cams={len(cams)} bus_month={bus_month} fare={'yes' if fare else 'no'} size={len(out)//1024}KB")
