"""自建论断库：任意出生信息 → 13 维本命解读（与 v4.0 数据集同格式）。
模型由 `xuan train` 用本机下载的 v4.0 数据集训练，存放在 XUAN_HOME/models（公开仓库不带模型）。"""
import sys, os, json, subprocess, collections, pickle
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(D, 'lib')); sys.path.insert(0, os.path.dirname(D))
import config as C
import chartfeat
from chartfeat import Chart, tokens_full
from derive import derived
from derive2 import derived2
from derive3 import derived3
from generate import TopicGen
from topics import TOPICS
import lookup
def features(key):
    p = subprocess.run([C.TSX, os.path.join(D, 'features.ts')], input=key + '\n', capture_output=True, text=True, cwd=C.ENGINE, env=C.env())
    if p.returncode: raise SystemExit(p.stderr[-2000:])
    return json.loads(p.stdout.strip().splitlines()[-1])
def have_models(topics):
    return all(os.path.exists(f'{C.MODELS}/{t}.pkl') for t in topics)
_G = {}
def gen(t):
    if t not in _G: _G[t] = TopicGen(pickle.load(open(f'{C.MODELS}/{t}.pkl', 'rb')))
    return _G[t]
def reading(f, topics):
    c = Chart(f); T = set(tokens_full(f)); d = derived(c); d.update(derived2(c)); d3, T3 = derived3(c); d.update(d3); T |= T3
    return {t: gen(t).text(T, d) for t in topics}
def compare(key, r):
    y, m, d, h, g = key.split('-')
    o = lookup.find(int(y), int(m), int(d), int(h), g)
    if not o: return None
    rows = []
    for t, x in r.items():
        gold = o['c'][t]
        a = collections.Counter(l for l in x.split('\n') if l.strip()); b = collections.Counter(l for l in gold.split('\n') if l.strip())
        tp = sum((a & b).values())
        rows.append(dict(topic=t, exact=x == gold, P=tp / max(1, sum(a.values())), R=tp / max(1, sum(b.values()))))
    return rows
