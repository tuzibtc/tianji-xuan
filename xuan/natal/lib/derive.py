"""由盘面派生出现在模板行里的字符串（星曜描述、星名串、辅星串、大限年龄段等）。"""
from chartfeat import Chart, PAL_ORDER, BR, SHA6
LBL = {'B': '（庙旺）', 'D': '（落陷）'}
def bcls(cls):
    return {'bright':'B','dim':'D'}.get(cls, 'N')
def star_label(s):
    nm, ty, raw, cls, hua = s
    return nm + (('化' + hua) if hua else '') + LBL.get(bcls(cls), '')
def derived(c: Chart):
    out = {}
    for p in c.f['P']:
        n = p['n']; maj = c.majors(p)
        out['D:' + n] = '、'.join(star_label(s) for s in maj)
        out['N:' + n] = '、'.join(s[0] for s in maj)
        out['A:' + n] = '、'.join(s[0] for s in p['st'] if s[1] != 'major')
        out['S:' + n] = '、'.join(s[0] for s in p['st'] if s[0] in SHA6)
        ps = [p, *c.sanhe(n), c.opp(n)]
        out['SF:' + n] = str(sum(1 for q in ps for s in q['st'] if s[0] in SHA6))
    dx = c.cur_dx()
    if dx >= 0:
        s, e, b = c.f['dx'][dx]
        out['DXR1'] = f'{s}–{e}'; out['DXR2'] = f'{s}-{e}'
    return out
