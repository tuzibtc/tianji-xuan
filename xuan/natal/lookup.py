"""13 维解读数据集 v4.0 查询（本命盘，1950–2026；CC BY 4.0，由 xuan setup 从上游 Releases 下载到 XUAN_HOME）。
数据集按时辰序号直接排盘、不做真太阳时；钟表时间由 xuan 先经引擎换算成时辰再来查。"""
import io, json, os
import config as C
LBL = {'overview': '命格总览', 'personality': '性格特质', 'love': '感情婚姻', 'career': '事业职业', 'wealth': '财富运势', 'health': '健康状况', 'family': '兄弟合伙',
       'children': '子女缘分', 'move': '迁移外出', 'friends': '人际贵人', 'home': '田宅不动产', 'spirit': '精神福德', 'parents': '父母长辈'}
def available(y):
    return os.path.exists(f'{C.DATASET}/year-{y}.jsonl.zst')
def find(y, m, d, h, g):
    import zstandard
    p = f'{C.DATASET}/year-{y}.jsonl.zst'
    if not os.path.exists(p): return None
    key = f'{y}-{m:02d}-{d:02d}-{h}-{g}'; prefix = '{"k":"%s"' % key
    with open(p, 'rb') as f:
        r = io.TextIOWrapper(zstandard.ZstdDecompressor(max_window_size=2**27).stream_reader(f), encoding='utf-8')
        for line in r:
            if line.startswith(prefix) or line[:60].find(key) >= 0:
                o = json.loads(line)
                if o['k'] == key: return o
    return None
