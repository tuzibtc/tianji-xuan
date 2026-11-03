"""规则学习（numpy 位图版）：单元 (section, template, occ) ← 盘面 token 的 DNF。"""
import numpy as np, collections

class BitData:
    def __init__(self, token_lists, vocab):
        self.N = len(token_lists); self.V = len(vocab)
        rows = np.zeros((self.N, self.V), dtype=bool)
        for i, tl in enumerate(token_lists): rows[i, tl] = True
        self.R = np.packbits(rows, axis=1)            # N x V/8
        self.C = np.packbits(rows.T, axis=1)          # V x N/8
        self.freq = rows.sum(0)
        del rows
        self.allbits = np.packbits(np.ones(self.N, dtype=bool))
    def pbits(self, ids):
        b = np.zeros(self.N, dtype=bool); b[ids] = True; return np.packbits(b)
    def inter(self, ids):
        r = np.bitwise_and.reduce(self.R[ids], axis=0)
        return np.flatnonzero(np.unpackbits(r)[:self.V])
    def andcols(self, toks):
        b = self.allbits.copy()
        for t in toks: b &= self.C[t]
        return b

def learn_rules(bd, units_pos, dependent, max_depth=6, dontcare=None):
    dontcare = dontcare or {}
    rules = {}; unexplained = {}
    def conj_for(ids, P, notP, extra):
        it = set(bd.inter(ids).tolist()) | set(extra)
        bits = bd.allbits.copy(); conj = []
        for t in sorted(it, key=lambda x: bd.freq[x]):
            nb = bits & bd.C[t]
            if not np.array_equal(nb, bits): bits = nb; conj.append(t)
            if not (bits & notP).any(): break
        if (bits & notP).any(): return None
        k = 0
        while k < len(conj) and len(conj) > 1:
            b2 = bd.andcols([t for j, t in enumerate(conj) if j != k])
            if not (b2 & notP).any(): conj.pop(k)
            else: k += 1
        return tuple(sorted(conj))
    POP = np.array([bin(i).count('1') for i in range(256)], dtype=np.uint16)
    def pc_rows(M, mask):
        return POP[M & mask].sum(axis=1)
    def foil(P, notP, maxr=24, maxlen=8, ncand=32):
        rl = []; remaining = P.copy()
        while remaining.any() and len(rl) < maxr:
            cover = bd.allbits.copy(); conj = []
            p0 = int(POP[cover & remaining].sum()); n0 = int(POP[cover & notP].sum())
            while n0 > 0 and len(conj) < maxlen:
                def est(mask):
                    idx = np.flatnonzero(np.unpackbits(mask)[:bd.N]); n = len(idx)
                    if n > 3000: idx = idx[:: n // 3000 + 1]
                    if len(idx) == 0: return np.zeros(bd.V)
                    return np.unpackbits(bd.R[idx], axis=1)[:, :bd.V].sum(0) * (n / len(idx))
                ppe = est(cover & remaining); nne = est(cover & notP)
                ge = ppe * (np.log2((ppe + 1e-9) / (ppe + nne + 1e-9)) - np.log2(p0 / (p0 + n0)))
                ge[ppe == 0] = -1e18; ge[conj] = -1e18
                cands = np.argsort(-ge)[:ncand]; cands = cands[ge[cands] > 0]
                if len(cands) == 0: break
                pp = POP[bd.C[cands] & (cover & remaining)].sum(1).astype(np.float64)
                nn = POP[bd.C[cands] & (cover & notP)].sum(1).astype(np.float64)
                gain = pp * (np.log2((pp + 1e-9) / (pp + nn + 1e-9)) - np.log2(p0 / (p0 + n0)))
                gain[pp == 0] = -1e18
                j = int(gain.argmax())
                if gain[j] <= 0: break
                t = int(cands[j]); conj.append(t); cover &= bd.C[t]
                p0 = int(POP[cover & remaining].sum()); n0 = int(POP[cover & notP].sum())
            if n0 > 0 or p0 == 0: break
            rl.append(tuple(sorted(conj))); remaining &= ~cover
        return rl
    def dnf(ids, P, notP, extra, depth):
        c = conj_for(ids, P, notP, extra)
        if c is not None: return [c]
        if depth == 0: return foil(P, notP)
        if depth >= max_depth or len(ids) < 2: return []
        sub = ids if len(ids) <= 4000 else ids[:: len(ids) // 4000 + 1]
        cnt = np.unpackbits(bd.R[sub], axis=1)[:, :bd.V].sum(0)
        n = len(sub)
        score = np.minimum(cnt, n - cnt)
        best = int(score.argmax())
        if score[best] == 0: return []
        col = np.unpackbits(bd.C[best])[:bd.N].astype(bool)
        ids = np.asarray(ids)
        a = ids[col[ids]]; b = ids[~col[ids]]
        return dnf(a, P, notP, tuple(extra) + (best,), depth + 1) + dnf(b, P, notP, extra, depth + 1)
    import time, sys
    t0 = time.time()
    for ui, (u, ids) in enumerate(units_pos.items()):
        if ui % 500 == 0: print('  unit', ui, '/', len(units_pos), '%.0fs' % (time.time() - t0), file=sys.stderr, flush=True)
        if u in dependent: continue
        ids = np.asarray(ids)
        P = bd.pbits(ids); notP = ~P & bd.allbits
        if u in dontcare and len(dontcare[u]): notP &= ~bd.pbits(np.asarray(dontcare[u]))
        rl = dnf(ids, P, notP, (), 0)
        cov = np.zeros_like(P)
        for r in rl: cov |= bd.andcols(r)
        rules[u] = rl
        miss = int(np.unpackbits(P & ~cov).sum())
        if miss: unexplained[u] = miss
    return rules, unexplained

def learn_topic(token_lists, vocab, seqs, tails, prec_n=20000, dontcare_fn=None):
    from textmodel import is_header, section_key
    bd = BitData(token_lists, vocab)
    pos = collections.defaultdict(list); dsecs = collections.defaultdict(set)
    for i, seq in enumerate(seqs):
        for g, sec, tpl, occ, dsec in seq:
            u = (sec, tpl, occ); pos[u].append(i); dsecs[u].add(dsec)
    # 依附：标题类单元出现 ⟺ 只在其下出现的内容单元任一出现；'---' ⟺ 其后标题出现
    hdr_units = [u for u in pos if is_header(u[1])]
    owned = collections.defaultdict(list)
    for u, ds in dsecs.items():
        if not is_header(u[1]) and len(ds) == 1: owned[next(iter(ds))].append(u)
    dependent = {}
    N = len(seqs)
    for h in hdr_units:
        if len(pos[h]) == N: continue
        if h[1] == '---':
            nx = [d for d in dsecs[h]]
            if len(nx) == 1:
                tgt = nx[0][1:]
                hs = [u for u in hdr_units if u[1] == tgt]
                if len(hs) == 1 and set(pos[hs[0]]) >= set(pos[h]) and set(pos[hs[0]]) == set(pos[h]):
                    dependent[h] = ('H', hs[0])
            continue
        from textmodel import starts_section
        if starts_section(h[1]): key = section_key(h[1])
        else:
            if len(dsecs[h]) != 1: continue
            key = next(iter(dsecs[h]))
        S = owned.get(key, [])
        if not S: continue
        uni = set()
        for u in S: uni.update(pos[u])
        if uni == set(pos[h]): dependent[h] = ('S', tuple(S))
    dc = dontcare_fn(seqs, pos) if dontcare_fn else {}
    rules, unexplained = learn_rules(bd, pos, dependent, dontcare=dc)
    meanpos = collections.defaultdict(list); prec = collections.Counter()
    gaps = collections.defaultdict(collections.Counter); gap1 = collections.defaultdict(collections.Counter)
    for ci, seq in enumerate(seqs):
        seq = [x for x in seq if x[1] != '\x00GAP']
        L = len(seq); prev = None; us = []
        for i, (g, sec, tpl, occ, dsec) in enumerate(seq):
            u = (sec, tpl, occ); us.append(u); meanpos[u].append(i / max(1, L))
            gaps[(prev, u)][g] += 1; gap1[u][g] += 1; prev = u
        if ci < prec_n:
            for i in range(L):
                ui = us[i]
                for j in range(i + 1, L): prec[(ui, us[j])] += 1
    order = {u: sum(v) / len(v) for u, v in meanpos.items()}
    before = set(k for k in prec if (k[1], k[0]) not in prec)
    inv = {v: k for k, v in vocab.items()}
    named = {u: [tuple(inv[t] for t in r) for r in rl] for u, rl in rules.items()}
    freq = {inv[t]: int(bd.freq[t]) for t in range(len(vocab))}
    return dict(rules=named, unexplained=unexplained, dependent=dependent, order=order, before=before,
                gaps={k: v.most_common(1)[0][0] for k, v in gaps.items()}, gap1={k: v.most_common(1)[0][0] for k, v in gap1.items()},
                tail=collections.Counter(tails).most_common(1)[0][0], freq=freq, support={u: len(v) for u, v in pos.items()})
