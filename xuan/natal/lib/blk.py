"""截断组（逆推出的“每段最多 N 条”规则）：
  1) 关键推导块：〔倪师断法·X〕行最多 2 条，按类型展示先后为优先级；
  2) 《紫微斗数全书》卷二十二宫断语：「…条」引文最多 6 条，按平均先后为优先级。
训练时：组已满且末条优先级不低于某单元 → 该单元缺席不作反例（被截断，非“不成立”）。生成时：按优先级保留前 N 条。"""
import re, collections
CAP = 2; QCAP = 6
RX = re.compile(r'^· 〔倪师断法·([^〕]*)〕')
QX = re.compile(r'^· 《紫微斗数全书·卷二·[^》]*》[^：「]*条：')
def btype(tpl):
    m = RX.match(tpl); return m.group(1) if m else None
def isq(u): return u[0] == '▸Q' and bool(QX.match(u[1]))
def learn_rank(seqs):
    w = collections.Counter(); types = set(); qpos = collections.defaultdict(list)
    for seq in seqs:
        b = [btype(x[2]) for x in seq if btype(x[2])]
        types.update(b)
        for i in range(len(b)):
            for j in range(i + 1, len(b)):
                if b[i] != b[j]: w[b[i]] += 1; w[b[j]] -= 1
        q = [x[1:4] for x in seq if isq(x[1:4])]
        for i, u in enumerate(q): qpos[u].append(i)
    order = sorted(types, key=lambda t: -w[t]); r = {t: i for i, t in enumerate(order)}
    r['\x00Q'] = {u: sum(v) / len(v) for u, v in qpos.items()}
    return r
def make_dontcare(rank):
    qr = rank.get('\x00Q', {})
    def fn(seqs, pos):
        full = collections.defaultdict(list); qfull = []
        for i, seq in enumerate(seqs):
            b = [btype(x[2]) for x in seq if btype(x[2])]
            if len(b) >= CAP: full[max(rank[t] for t in b)].append(i)
            q = [x[1:4] for x in seq if isq(x[1:4])]
            if len(q) >= QCAP: qfull.append((max(qr.get(u, 0) for u in q), i))
        qfull.sort()
        dc = {}
        for u in pos:
            t = btype(u[1])
            if t is not None:
                ids = []
                for r, l in full.items():
                    if r < rank[t]: ids += l
                dc[u] = ids
            elif isq(u):
                me = qr.get(u, 99); dc[u] = [i for m, i in qfull if m <= me]
        return dc
    return fn
def cap(units, rank, order):
    b = [u for u in units if btype(u[1])]
    if len(b) > CAP:
        keep = set(sorted(b, key=lambda u: (rank.get(btype(u[1]), 99), order.get(u, .5)))[:CAP])
        units = {u for u in units if not btype(u[1]) or u in keep}
    q = [u for u in units if isq(u)]
    if len(q) > QCAP:
        qr = rank.get('\x00Q', {})
        keep = set(sorted(q, key=lambda u: (qr.get(u, 99), order.get(u, .5)))[:QCAP])
        units = {u for u in units if not isq(u) or u in keep}
    return units
