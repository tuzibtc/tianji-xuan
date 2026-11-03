"""xuan train：用本机下载的 v4.0 数据集训练自建论断库（存到 XUAN_HOME/models），覆盖数据集范围外（1950 年前 / 2027 年后）出生的人。
步骤：每年抽样 → 引擎排盘导出特征 → 派生特征 → 13 个专题逐个学习规则 → 留出集逐字评估（存到 XUAN_HOME/eval）。
全量默认参数大约需要 15 GB 内存、数小时；先用小参数试跑：xuan train --topics wealth --per-year 60 --ntrain 3000 --ntest 500"""
import collections, io, json, os, pickle, random, subprocess, sys, time, zlib
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D); sys.path.insert(0, os.path.join(D, 'natal', 'lib'))
import config as C
W = C.TRAIN_WORK
PAL12 = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄', '迁移', '仆役', '官禄', '田宅', '福德', '父母']
def zread(p):
    import zstandard
    f = open(p, 'rb')
    return io.TextIOWrapper(zstandard.ZstdDecompressor(max_window_size=2**27).stream_reader(f), encoding='utf-8')
def sample(per_year, seed=1):
    out = os.path.join(W, 'sample.jsonl'); keys = os.path.join(W, 'keys.txt')
    if os.path.exists(out) and os.path.exists(keys + '.done'): return
    rnd = random.Random(seed); n = 0
    with open(out, 'w') as w, open(keys, 'w') as kw:
        for y in range(1950, 2027):
            p = f'{C.DATASET}/year-{y}.jsonl.zst'
            if not os.path.exists(p): continue
            total = 8784 if y % 4 == 0 else 8760   # 天数 × 12 时辰 × 2 性别
            pick = set(rnd.sample(range(total), min(per_year, total)))
            for i, line in enumerate(zread(p)):
                if i in pick:
                    w.write(line); kw.write(json.loads(line)['k'] + '\n'); n += 1
    open(keys + '.done', 'w').write(str(n)); print('抽样', n, '张盘', flush=True)
def feats():
    out = os.path.join(W, 'pre.jsonl')
    if os.path.exists(out + '.done'): return
    from chartfeat import Chart, tokens_full
    from derive import derived
    from derive2 import derived2
    from derive3 import derived3
    p = subprocess.Popen([C.TSX, os.path.join(D, 'natal', 'features.ts')], stdin=open(os.path.join(W, 'keys.txt')), stdout=subprocess.PIPE, text=True, cwd=C.ENGINE, env=C.env())
    n = 0
    with open(out, 'w') as w:
        for l in p.stdout:
            f = json.loads(l); c = Chart(f); d = derived(c); d.update(derived2(c)); d3, T3 = derived3(c); d.update(d3)
            w.write(json.dumps({'k': f['k'], 'T': sorted(set(tokens_full(f)) | set(T3)), 'd': d}, ensure_ascii=False) + '\n'); n += 1
    if p.wait(): sys.exit('features.ts 失败')
    open(out + '.done', 'w').write(str(n)); print('特征', n, flush=True)
def role_keys(topic):
    from topics import TOPIC_PAL
    n = TOPIC_PAL[topic]; i = PAL12.index(n)
    first = [n, PAL12[(i - 4) % 12], PAL12[(i - 8) % 12], PAL12[(i + 6) % 12]]
    ks = []
    for nm in first + [x for x in PAL12 if x not in first]: ks += ['D:' + nm, 'N:' + nm, 'A:' + nm, 'S:' + nm, 'SF:' + nm, 'J:' + nm, 'HJ:' + nm, 'M1:' + nm]
    return ks + ['DXR1', 'DXR2', 'DXH', 'TMK', 'WPX1', 'WPX2', 'WPXB1', 'WPXB2', 'WPXB3', 'WSPL', 'WSPLB', 'HJX']
def norm(t):
    """评估时忽略可选的〔词义〕/免责行（公开版不带这两张表）。"""
    return '\n'.join(l for l in t.split('\n') if not l.startswith(('〔词义〕', '（古籍格局属')))
def train_topic(topic, NTR, NTE):
    from textmodel import build_sub, parse
    from learn_np import learn_topic
    from generate import TopicGen
    from glossary import strip_gloss
    from blk import learn_rank, make_dontcare
    os.makedirs(C.MODELS, exist_ok=True); os.makedirs(C.EVAL, exist_ok=True)
    ROLE = role_keys(topic); t0 = time.time()
    is_test = lambda k: zlib.crc32(k.encode()) % 8 == 0
    keys = sorted(open(os.path.join(W, 'keys.txt')).read().split())
    test = set([k for k in keys if is_test(k)][:NTE]); train = set([k for k in keys if not is_test(k)][:NTR])
    texts = {}
    for line in open(os.path.join(W, 'sample.jsonl')):
        o = json.loads(line)
        if o['k'] in train or o['k'] in test: texts[o['k']] = o['c'][topic]
    vocab = {}; toks = []; seqs = []; tails = []; testset = []
    for l in open(os.path.join(W, 'pre.jsonl')):
        o = json.loads(l); k = o['k']
        if k in train:
            toks.append([vocab.setdefault(t, len(vocab)) for t in o['T']])
            rx, seen = build_sub(o['d'], ROLE)
            seq, tail = parse(strip_gloss(texts.pop(k)), rx, seen); seqs.append(seq); tails.append(tail)
        elif k in test: testset.append((k, o['T'], o['d'], texts.pop(k)))
    print(topic, 'train', len(seqs), 'test', len(testset), 'vocab', len(vocab), flush=True)
    rank = learn_rank(seqs)
    pc = collections.defaultdict(collections.Counter)
    for sq in seqs:
        for a, b in zip([None] + sq[:-1], sq): pc[(a[1:4] if a else None, b[1:4])][b[0]] += 1
    pmode = {k: c.most_common(1)[0][0] for k, c in pc.items()}
    for sq in seqs:
        extra = []
        for a, b in zip([None] + sq[:-1], sq):
            k = (a[1:4] if a else None, b[1:4])
            if b[0] != pmode[k] and pc[k][b[0]] >= 3: extra.append((0, '\x00GAP', repr((b[0], k)), 1, '\x00'))
        sq.extend(extra)
    m = learn_topic(toks, vocab, seqs, tails, dontcare_fn=make_dontcare(rank))
    m['topic'] = topic; m['gloss'] = True; m['blk_rank'] = rank; m['pmode'] = pmode
    tb = collections.defaultdict(collections.Counter)
    for sq, tl in zip(seqs, tails):
        sq = [x for x in sq if x[1] != '\x00GAP']
        if sq: tb[sq[-1][1:4]][tl] += 1
    m['tail_by'] = {u: c.most_common(1)[0][0] for u, c in tb.items()}
    del toks, seqs
    pickle.dump(m, open(f'{C.MODELS}/{topic}.pkl', 'wb'), protocol=5)
    g = TopicGen(m); ex = 0; tp = fp = fn = 0
    for k, T, d, gold in testset:
        outp = norm(g.text(set(T), d)); gold = norm(gold); ex += outp == gold
        a = collections.Counter(x for x in outp.split('\n') if x.strip()); b = collections.Counter(x for x in gold.split('\n') if x.strip())
        tp += sum((a & b).values()); fp += sum((a - b).values()); fn += sum((b - a).values())
    n = max(1, len(testset))
    res = dict(topic=topic, ntrain=len(train), ntest=len(testset), exact=ex / n, P=tp / max(1, tp + fp), R=tp / max(1, tp + fn), secs=round(time.time() - t0))
    json.dump(res, open(f'{C.EVAL}/{topic}.json', 'w'), ensure_ascii=False, indent=1)
    print(topic, '留出集逐字一致 %.4f  行精确率 %.4f  行召回 %.4f  %ds' % (res['exact'], res['P'], res['R'], res['secs']), flush=True)
def main(a):
    from topics import TOPICS
    if not os.path.isdir(C.DATASET) or not any(f.endswith('.zst') for f in os.listdir(C.DATASET)): sys.exit('先运行 xuan setup 下载数据集')
    if not os.path.exists(C.TSX): sys.exit('先运行 xuan setup 安装引擎')
    os.makedirs(W, exist_ok=True)
    topics = a.topics.split(',') if a.topics else TOPICS
    sample(a.per_year); feats()
    procs = []
    for t in topics:
        while len([p for p in procs if p.poll() is None]) >= a.jobs: time.sleep(2)
        procs.append(subprocess.Popen([C.PY, os.path.abspath(__file__), '--worker', t, str(a.ntrain), str(a.ntest)], env=C.env()))
    rc = [p.wait() for p in procs]
    if any(rc): sys.exit(f'有专题训练失败：{rc}')
    print('训练完成，模型在', C.MODELS)
if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--worker':
    train_topic(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
