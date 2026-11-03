"""由引擎特征(JSON) 生成规则用的离散特征 token。"""
BR = '子丑寅卯辰巳午未申酉戌亥'
PAL_ORDER = ['命宫','兄弟','夫妻','子女','财帛','疾厄','迁移','仆役','官禄','田宅','福德','父母']
GEN_YEAR, GEN_MONTH, GEN_DAY = 2026, 10, 15   # 数据集生成日（当前大限按此算）

def bclass(raw):
    return {'庙':'B','旺':'B','得':'N','利':'N','平':'N','闲':'D','不':'D','陷':'D'}.get(raw, '_')

class Chart:
    def __init__(self, f):
        self.f = f
        self.P = {p['n']: p for p in f['P']}
        self.byb = {p['b']: p for p in f['P']}
    def pal(self, n): return self.P[n]
    def opp(self, n): return self.byb[(self.P[n]['b'] + 6) % 12]
    def sanhe(self, n):
        b = self.P[n]['b']; return self.byb[(b + 4) % 12], self.byb[(b + 8) % 12]
    def majors(self, p): return [s for s in p['st'] if s[1] == 'major']
    def nominal_age(self):
        y = int(self.f['k'][:4])
        # 虚岁：生成日 - 农历生年 + 1 ；农历生年=公历年（春节前出生者 -1）用 dx 不易得 → 由 features 的 ys/yb 推
        ly = self.lunar_year()
        return GEN_YEAR - ly + 1
    def lunar_year(self):
        y = int(self.f['k'][:4])
        # 年支 yb 与公历年支比较
        if (y - 4) % 12 == self.f['yb']: return y
        return y - 1
    def cur_dx(self):
        a = self.nominal_age()
        for i, (s, e, b) in enumerate(self.f['dx']):
            if s <= a <= e: return i
        return -1

def tokens(f):
    c = Chart(f); T = set()
    T.add('g:' + f['g']); T.add('ju:' + f['ju']); T.add('mz:' + str(f['mz'])); T.add('sz:' + str(f['sz'])); T.add('yyg:' + str(f['yyg']))
    T.add('ys:%d' % f['ys']); T.add('yb:%d' % f['yb'])
    for p in f['P']:
        n = p['n']; T.add(f'{n}@{BR[p["b"]]}')
        if p['shen']: T.add(f'shen:{n}')
        maj = c.majors(p)
        if not maj: T.add(f'{n}:empty')
        else: T.add(f'{n}:first={maj[0][0]}'); T.add(f'{n}:nmaj={len(maj)}')
        for s in p['st']:
            nm, ty, raw, cls, hua = s
            T.add(f'{n}:{nm}')
            if raw: T.add(f'{n}:{nm}:{raw}')
            T.add(f'{n}:{nm}:' + {'bright':'B','dim':'D','normal':'N'}.get(cls,'_'))
            if hua: T.add(f'{n}:{nm}:化{hua}'); T.add(f'{n}:化{hua}'); T.add(f'化{hua}@{n}')
        for x in p['self']: T.add(f'{n}:self:{x}')
        if not maj:
            for s in c.majors(c.opp(n)): T.add(f'{n}:borrow:{s[0]}')
    dx = c.cur_dx()
    if dx >= 0:
        b = f['dx'][dx][2]; T.add('curdx:' + c.byb[b]['n']); T.add('curdxi:%d' % dx)
    T.add('age:%d' % c.nominal_age())
    return T

SHA6 = ['擎羊','陀罗','火星','铃星','地空','地劫']
JI6 = ['左辅','右弼','文昌','文曲','天魁','天钺']
CHECK = SHA6 + JI6 + ['禄存','天马']
def tokens_ext(f):
    """tokens + 缺省/计数类 token（表达“没有某星”的条件）"""
    T = tokens(f)
    for p in f['P']:
        n = p['n']; names = set(s[0] for s in p['st'])
        for x in CHECK:
            if x not in names: T.add(f'{n}:no:{x}')
        hs = set(s[4] for s in p['st'] if s[4])
        for h in '禄权科忌':
            if h not in hs: T.add(f'{n}:no:化{h}')
        ns = sum(1 for x in SHA6 if x in names); T.add(f'{n}:nsha={ns}'); T.add(f'{n}:nsha>={min(ns,2)}' if ns else f'{n}:nsha0')
        nj = sum(1 for x in JI6 if x in names); T.add(f'{n}:nji={nj}')
    return T

def tokens_full(f):
    T = tokens_ext(f); c = Chart(f)
    for p in f['P']:
        n = p['n']; ps = [p, *c.sanhe(n), c.opp(n)]
        names = [s[0] for q in ps for s in q['st']]
        ns = sum(1 for x in names if x in SHA6); nj = sum(1 for x in names if x in JI6)
        for k in range(1, 7):
            T.add(f'SF:{n}:nsha>={k}' if ns >= k else f'SF:{n}:nsha<{k}')
            T.add(f'SF:{n}:nji>={k}' if nj >= k else f'SF:{n}:nji<{k}')
        hs = set(s[4] for q in ps for s in q['st'] if s[4])
        for h in '禄权科忌':
            T.add(f'SF:{n}:化{h}' if h in hs else f'SF:{n}:no化{h}')
        for x in ('禄存', '天马') + tuple(SHA6) + tuple(JI6):
            if x in names: T.add(f'SF:{n}:{x}')
    return T
