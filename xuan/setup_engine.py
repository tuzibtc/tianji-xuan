"""xuan setup：
1) 克隆上游排盘引擎（engine.lock 里固定的 commit，不 fork、不改动）到 XUAN_HOME/engine；
2) 在引擎目录 npm ci（需要 node ≥ 18 和 git）；
3) 从上游 GitHub Releases 下载 13 维解读数据集 v4.0（CC BY 4.0），逐个文件校验 SHA256；
4) 没有人物库时，建一个空的 people.json。
环境变量：XUAN_ENGINE_URL 可改克隆地址（镜像 / 本地路径），XUAN_DATASET_BASE 可改下载地址（镜像）。"""
import hashlib, json, os, shutil, subprocess, sys, urllib.request
import config as C
def run(cmd, cwd=None):
    print('$', ' '.join(cmd), flush=True); subprocess.run(cmd, cwd=cwd, check=True)
def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def fetch(url, dst):
    tmp = dst + '.part'
    req = urllib.request.Request(url, headers={'User-Agent': 'xuan-setup'})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f: shutil.copyfileobj(r, f, 1 << 20)
    os.replace(tmp, dst)
def engine(force):
    L = C.lock(); url = os.environ.get('XUAN_ENGINE_URL', L['url']); commit = L['commit']
    E = C.ENGINE
    if os.path.isdir(os.path.join(E, '.git')) and not force:
        cur = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=E, capture_output=True, text=True).stdout.strip()
        if cur != commit: run(['git', 'fetch', '--quiet', 'origin'], E); run(['git', 'checkout', '--quiet', commit], E)
    else:
        if os.path.exists(E): shutil.rmtree(E)
        run(['git', 'clone', '--quiet', url, E]); run(['git', '-c', 'advice.detachedHead=false', 'checkout', '--quiet', commit], E)
    if not os.path.exists(C.TSX) or force:
        run(['npm', 'ci', '--no-audit', '--no-fund', '--loglevel=error'], E)
    print('引擎就绪：', E, '@', commit[:12])
def dataset(years, force):
    base = os.environ.get('XUAN_DATASET_BASE', C.lock()['dataset_base']).rstrip('/')
    os.makedirs(C.DATASET, exist_ok=True)
    sums = os.path.join(C.DATASET, 'SHA256SUMS.txt')
    for f in ('SHA256SUMS.txt', 'MANIFEST.json'):
        if force or not os.path.exists(os.path.join(C.DATASET, f)): fetch(f'{base}/{f}', os.path.join(C.DATASET, f))
    want = [l.split() for l in open(sums) if l.strip()]
    if years:
        lo, hi = (int(x) for x in (years.split('-') + [years])[:2])
        want = [(h, n) for h, n in want if lo <= int(n[5:9]) <= hi]
    bad = []
    for i, (h, n) in enumerate(want, 1):
        p = os.path.join(C.DATASET, n)
        if os.path.exists(p) and not force and sha256(p) == h: continue
        print(f'下载 [{i}/{len(want)}] {n}', flush=True); fetch(f'{base}/{n}', p)
        if sha256(p) != h: bad.append(n); os.remove(p)
    if bad: sys.exit('SHA256 校验失败：' + ', '.join(bad))
    print(f'数据集就绪：{len(want)} 个年份文件，SHA256 全部通过（{C.DATASET}）')
def main(a):
    os.makedirs(C.HOME, exist_ok=True)
    for tool in ('git', 'node', 'npm'):
        if not shutil.which(tool): sys.exit(f'缺少 {tool}，请先安装（node ≥ 18）')
    try: import zstandard  # noqa
    except ImportError: sys.exit(f'缺少 Python 包 zstandard：{C.PY} -m pip install -r requirements.txt')
    engine(a.force)
    if not a.no_dataset: dataset(a.years, a.force)
    if not os.path.exists(C.PEOPLE):
        json.dump([], open(C.PEOPLE, 'w')); print('已创建空的人物库：', C.PEOPLE, '（格式见仓库里的 people.example.json）')
    os.makedirs(C.LOGS, exist_ok=True)
    print('完成。数据目录：', C.HOME)
