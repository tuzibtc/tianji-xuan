"""运限生成器：大限 / 流年（小限：生年支三合起 1 岁、男顺女逆、虚岁）/ 流月（斗君）。
只输出分数；吉凶阈值没有经过验证，所以 xuan 只报一生里的相对位置（百分位）。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rules import RULES, SIX_LUCKY, SIX_SHA
BR = '子丑寅卯辰巳午未申酉戌亥'
CH = {}   # 由 xuan 即时排盘后放进来（公开版不带任何人的盘）
OFF = {'命': 0, '财帛': -4, '官禄': 4, '夫妻': -2, '福德': 2, '疾厄': -5, '迁移': 6}

def pal(c, b):
    return next(p for p in c['palaces'] if p['branch'] == b % 12)

def has_ziwei(c, b):
    return any(s['n'] == '紫微' for x in (b, b + 6) for s in pal(c, x)['stars'])

def score_palace(c, b, weight, fired, role, opp=False):
    p = pal(c, b); s = 0.0; zw = has_ziwei(c, b if not opp else b + 6)
    def add(v, rid, why):
        nonlocal s
        s += v * weight; fired.append((rid, role, p['bz'] + p['name'], why, round(v * weight, 2)))
    stars = p['stars']
    if p['isEmpty'] and p['borrowed']:
        stars = stars + [dict(s2, borrowed=1) for s2 in pal(c, b + 6)['stars'] if s2['t'] == 'major']
    for st in stars:
        k = RULES['S12']['w'] if st.get('borrowed') else 1.0
        n, h, br = st['n'], st['h'], st['b']
        if h == '禄': add(RULES['S1']['w'] * k, 'S1', n + '化禄')
        if h == '权': add(RULES['S2']['w'] * k, 'S2', n + '化权')
        if h == '科': add(RULES['S3']['w'] * k, 'S3', n + '化科')
        if h == '忌':
            v = RULES['S4']['w'] * k * (0.5 if zw else 1) * ((1 / 0.8) if opp else 1)
            add(v, 'S4' + ('+S9' if zw else '') + ('+S13' if opp else ''), n + '化忌')
        if st.get('borrowed'): continue
        if n == '禄存': add(RULES['S5']['w'], 'S5', '禄存')
        if n in SIX_LUCKY: add(RULES['S6']['w'], 'S6', n)
        if n in SIX_SHA:
            m = 0.5 if br in ('庙', '旺') else (1.5 if br == '陷' else 1.0)
            v = RULES['S7']['w'] * m * (0.5 if zw else 1)
            add(v, 'S7+S8' + ('+S9' if zw else ''), n + br)
        if st['t'] == 'major':
            if br in ('庙', '旺'): add(RULES['S11']['w'], 'S11', n + br)
            elif br == '陷': add(-RULES['S11']['w'], 'S11', n + br)
    return s

def view(c, L, kind, fired, role):
    s = score_palace(c, L, 1.0, fired, role) + score_palace(c, L + 6, 0.8, fired, role + '·对宫', opp=True)
    if kind == 'decade':
        s += score_palace(c, L + 4, 0.5, fired, role + '·三合') + score_palace(c, L - 4, 0.5, fired, role + '·三合')
        s += score_palace(c, L + 1, 0.3, fired, role + '·夹') + score_palace(c, L - 1, 0.3, fired, role + '·夹')
    return s

TOPICS = ('overall', 'wealth', 'career', 'love', 'health', 'siblings', 'children')
def topics(c, L, kind):
    out, fired = _topics_v1(c, L, kind)
    return v2_adjust(c, L, kind, out, fired)

def _topics_v1(c, L, kind):
    fired = []; out = {}
    out['overall'] = view(c, L, kind, fired, '限命')
    out['wealth'] = view(c, L + OFF['财帛'], kind, fired, '限财帛')
    out['career'] = view(c, L + OFF['官禄'], kind, fired, '限官禄')
    lv = view(c, L + OFF['夫妻'], kind, fired, '限夫妻'); fu = view(c, L + OFF['福德'], kind, fired, '限福德')
    out['love'] = (lv + fu) / 2; fired.append(('T5', '感情', '', '夫妻宫与福德宫并看', 0))
    for b in (L + OFF['夫妻'], L + OFF['福德']):
        p = pal(c, b); names = {s['n'] for s in p['stars']}
        if '廉贞' in names and names & {'破军', '贪狼'} or any(s['h'] == '忌' for s in p['stars']):
            out['love'] += RULES['T6']['w']; fired.append(('T6', '感情', p['bz'] + p['name'], '廉破/廉贪或化忌', RULES['T6']['w']))
    hv = view(c, L + OFF['疾厄'], kind, fired, '限疾厄')
    sha_here = sum(1 for s in pal(c, L)['stars'] if s['n'] in SIX_SHA)
    out['health'] = hv - 0.5 * sha_here
    if pal(c, L)['name'] == '疾厄':
        out['health'] += RULES['T1']['w']; fired.append(('T1', '健康', '', '限落本命疾厄', RULES['T1']['w']))
    if c['input']['gender'] == 'male':
        for b in (L, L + 6, L + OFF['夫妻']):
            if any(s['n'] == '太阴' and s['h'] == '忌' for s in pal(c, b)['stars']):
                out['love'] += RULES['T7']['w']; fired.append(('T7', '感情', pal(c, b)['bz'], '男命太阴化忌', RULES['T7']['w']))
    for b in (L, L + 6, L + OFF['夫妻']):
        if any(s['n'] in ('红鸾', '天喜') for s in pal(c, b)['stars']):
            out['love_event'] = True; fired.append(('T4', '感情', pal(c, b)['bz'], '红鸾/天喜', 0))
    return out, fired

def v2_adjust(c, L, kind, out, fired):
    from rules import RULES_V3 as R
    here, opp = pal(c, L), pal(c, L + 6)
    both = here['stars'] + opp['stars']
    def f(rid, topic, v, why):
        out[topic] = out.get(topic, 0) + v; fired.append((rid, topic, here['bz'], why, v))
    if any(s['h'] == '忌' for s in opp['stars']): f('R-A', 'overall', R['R-A']['w'], '化忌在对宫冲限')
    if any(s['h'] == '忌' for s in here['stars']): f('R-B', 'overall', R['R-B']['w'], '限宫本宫化忌')
    luan = any(s['n'] in ('红鸾', '天喜') for s in both)
    ji = any(s['h'] == '忌' for s in both)
    sha_n = sum(1 for s in both if s['n'] in SIX_SHA)
    sp0 = '太阴' if c['input']['gender'] == 'male' else '太阳'
    spbad = any(s['n'] == sp0 and (s['h'] == '忌' or s['b'] == '陷') for s in both)
    lianpo = any(s['n'] == '廉贞' for s in both) and any(s['n'] in ('破军', '贪狼') and s['b'] in ('陷', '平', '闲', '不') for s in both)
    if luan and not ji and (sha_n >= 2 or spbad or lianpo):
        f('R-C3', 'love', R['R-C3']['w'], '红鸾动但逢煞/配偶星陷/廉破廉贪：婚变或婚而不好'); out['love_change'] = True
    elif luan and not ji: f('R-C', 'love', R['R-C']['w'], '红鸾会天喜：婚恋喜事'); out['love_marry'] = True
    if luan and ji: out['love_change'] = True
    if luan and ji: f('R-C2', 'love', R['R-C2']['w'], '红鸾天喜逢化忌，婚事不成')
    sp = '太阴' if c['input']['gender'] == 'male' else '太阳'
    if any(s['n'] == sp and (s['h'] == '忌' or s['b'] == '陷') for s in both): f('R-D', 'love', R['R-D']['w'], sp + '化忌/落陷在限宫或对宫')
    if any(s['n'] in ('地空', '地劫') for s in both): f('R-G', 'overall', R['R-G']['w'], '空劫在限宫/对宫'); f('R-G', 'wealth', R['R-G']['w'], '空劫耗财')
    if here['name'] == '疾厄' and any(s['n'] in SIX_SHA or s['h'] == '忌' for s in both): f('R-F', 'health', R['R-F']['w'], '限走疾厄见煞忌')
    for topic, nm in (('siblings', '兄弟'), ('children', '子女')):
        p = next(x for x in c['palaces'] if x['name'] == nm)
        k = 1.0 if (L % 12) in (p['branch'], (p['branch'] + 6) % 12) else 0.4
        sub = []
        v = view(c, p['branch'], 'year', sub, '本命' + nm) * k
        if any(s['h'] == '忌' for s in pal(c, p['branch'] + 6)['stars']): v += R['F1']['w'] * k
        out[topic] = v; fired.append(('F1', topic, p['bz'], f'本命{nm}宫（限{"到" if k == 1 else "未到"}）', round(v, 2)))
    return out, fired

def xusui(c, year): return year - c['lunar']['lunarYear'] + 1

def decade_of(c, year):
    a = xusui(c, year)
    return next((d for d in c['daxians'] if d['s'] <= a <= d['e']), None)

def xiaoxian(c, year):
    yb = c['yearBranch']; start = {2: 4, 6: 4, 10: 4, 8: 10, 0: 10, 4: 10, 5: 7, 9: 7, 1: 7, 11: 1, 3: 1, 7: 1}[yb]
    step = 1 if c['input']['gender'] == 'male' else -1
    return (start + step * (xusui(c, year) - 1)) % 12

def doujun(c, year):
    yb = (year - 4) % 12; m = abs(c['lunar']['lunarMonth'])
    return (yb - (m - 1) + c['hour']) % 12

def reading(c, kind, year=None, month=None):
    res = {'kind': kind}
    if kind == 'decade':
        d = decade_of(c, year); L = d['branch']; res['range'] = f"{d['s']}-{d['e']}岁"
    elif kind == 'year':
        L = xiaoxian(c, year); d = decade_of(c, year)
    else:
        L = (doujun(c, year) + month - 1) % 12; d = decade_of(c, year)
    sc, fired = topics(c, L, 'decade' if kind == 'decade' else 'year')
    res.update(palace=pal(c, L)['bz'] + '·本命' + pal(c, L)['name'], raw={k: round(v, 2) for k, v in sc.items() if k != 'love_event'})
    if kind != 'decade' and d:
        dsc, _ = topics(c, d['branch'], 'decade')
        res['decade_palace'] = pal(c, d['branch'])['bz'] + '·本命' + pal(c, d['branch'])['name']
        comb = {k: 0.6 * sc[k] + 0.4 * dsc[k] for k in TOPICS}
        if d['branch'] == L:
            comb = {k: v * 1.5 for k, v in comb.items()}; fired.append(('T2', '总', '', '大小二限同宫', 0))
    else:
        comb = {k: sc[k] for k in TOPICS}
    from rules import RULES_V3 as R
    d0 = decade_of(c, year)
    if d0:
        nxt = next((x for x in c['daxians'] if x['s'] == d0['e'] + 1), None)
        if nxt:
            ns, _ = topics(c, nxt['branch'], 'decade')
            if ns['overall'] <= -1.5:
                comb['overall'] += R['R-E']['w']; comb['health'] += R['R-E']['w'] / 2; fired.append(('R-E', 'overall', '', '未来十年无大运，大限在前十年', R['R-E']['w']))
    res['score'] = {k: round(v, 2) for k, v in comb.items()}
    res['focus'] = pal(c, L)['name']  # V6 宫性
    res['love_event'] = bool(sc.get('love_event')); res['love_marry'] = bool(sc.get('love_marry')); res['love_change'] = bool(sc.get('love_change'))
    res['facts'] = fired
    return res

