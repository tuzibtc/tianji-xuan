"""派生串 · 第二批（紫微解厄煞星串 J:、化忌对冲 HJ:、当前大限宫本命四化 DXH）。
从 v4 数据逆推格式；不改 derive.py 的既有输出。"""
JIEE_SHA = ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫', '天空']
JIEE_DESC = {'擎羊': '刃·血光', '陀罗': '拖磨·暗损', '火星': '急躁·突发', '铃星': '阴火·暗克', '地空': '空亡', '地劫': '劫夺破财', '天空': '虚耗'}
def derived2(c):
    out = {}
    for p in c.f['P']:
        n = p['n']
        j = [s[0] for s in p['st'] if s[0] in JIEE_SHA]
        if j: out['J:' + n] = '、'.join(f'{s}({JIEE_DESC[s]})' for s in j)
        mj = c.majors(p)
        if mj: out['M1:' + n] = mj[0][0]
        o = c.opp(n)
        hj = [s[0] for s in o['st'] if s[4] == '忌']
        if hj: out['HJ:' + n] = '、'.join(f"{o['n']}宫·{s}化忌" for s in hj)
    for p in c.f['P']:
        if any(s[0] == '天马' for s in p['st']):
            names = {s[0] for s in p['st']}
            k = [x for x in ('地空', '地劫', '旬空', '截空') if x in names]
            if k: out['TMK'] = '、'.join(k)
    dx = c.cur_dx()
    if dx >= 0:
        b = c.f['dx'][dx][2]; p = c.byb[b]
        h = [s[0] + '化' + s[4] for s in p['st'] if s[4] and s[1] == 'major']
        if h: out['DXH'] = '、'.join(h)
    return out
