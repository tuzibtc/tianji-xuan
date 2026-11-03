import functools, collections, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textmodel import render, build_sub
from derive import derived
from derive2 import derived2
from derive3 import derived3
from chartfeat import Chart, tokens_ext, tokens_full
from topics import role_order
from glossary import add_gloss

class TopicGen:
    def __init__(self, m, topic=None):
        self.m = m; self.topic = topic or m.get('topic'); self.anchor = collections.defaultdict(list); self.always = []
        fq = m.get('freq', {})
        for u, rl in m['rules'].items():
            for r in rl:
                r = frozenset(r)
                if not r: self.always.append(u); continue
                t = min(r, key=lambda x: fq.get(x, 0))
                self.anchor[t].append((r, u))
    def select(self, T):
        sel = set(self.always)
        for t in T:
            for r, u in self.anchor.get(t, ()):
                if u not in sel and r <= T: sel.add(u)
        dep = self.m.get('dependent', {})
        for u, (kind, x) in dep.items():
            if kind == 'S' and any(v in sel for v in x): sel.add(u)
        for u, (kind, x) in dep.items():
            if kind == 'H' and x in sel: sel.add(u)
        if 'blk_rank' in self.m:
            from blk import cap
            sel = cap(sel, self.m['blk_rank'], self.m['order'])
            for u, (kind, x) in dep.items():
                if kind == 'S' and u in sel and not any(v in sel for v in x): sel.discard(u)
        return sel
    def order(self, units):
        """拓扑排序：训练中“从未反序”的先后关系为硬约束，同层按平均相对位置。"""
        import heapq
        before, mp = self.m['before'], self.m['order']
        us = list(units); idx = {u: i for i, u in enumerate(us)}
        succ = collections.defaultdict(list); indeg = collections.Counter()
        for a in us:
            for b in us:
                if a is not b and (a, b) in before: succ[a].append(b); indeg[b] += 1
        key = lambda u: (mp.get(u, .5), idx[u])
        h = [(key(u), idx[u]) for u in us if indeg[u] == 0]; heapq.heapify(h); out = []; done = set()
        while len(out) < len(us):
            if not h:   # 有环：取剩余里位置最靠前的
                u = min((u for u in us if u not in done), key=key); indeg[u] = 0
            else:
                u = us[heapq.heappop(h)[1]]
                if u in done: continue
            done.add(u); out.append(u)
            for v in succ[u]:
                indeg[v] -= 1
                if indeg[v] == 0 and v not in done: heapq.heappush(h, (key(v), idx[v]))
        return out
    def text(self, T, d):
        import re
        sel = {u for u in self.select(T) if all(k in d for k in re.findall(r'\{([A-Z0-9]+(?::[^}]+)?)\}', u[1]))}
        import ast
        gapov = {}
        for u in [u for u in sel if u[0] == '\x00GAP']:
            g, k = ast.literal_eval(u[1]); gapov[k] = g; sel.discard(u)
        us = self.order(sel); parts = []; prev = None
        for u in us:
            g = gapov.get((prev, u), self.m['gaps'].get((prev, u), self.m['gap1'].get(u, 1)))
            parts += [''] * g + [render(u[1], d)]; prev = u
        out = '\n'.join(parts + [''] * self.m.get('tail_by', {}).get(prev, self.m['tail']))
        from disc import fix_disc
        out = fix_disc(out, self.topic)
        return add_gloss(out, self.topic) if self.m.get('gloss') else out
