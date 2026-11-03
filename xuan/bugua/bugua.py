#!/usr/bin/env python3
"""卜卦：六枚铜板一次成卦（由下往上读，人头/国徽面为阳，无动爻）；有疑才卜，每位问事人每天最多 3 卦。
  xuan bugua cast --asker 用户 --q "问题"                 # 机器随机掷（secrets）
  xuan bugua cast --asker 用户 --q "问题" --coins 101100  # 用户自己掷的结果（由下往上，1=阳）
  xuan bugua cast ... --test                              # 试跑：不计入每日次数和校准
  xuan bugua feedback <id> --verdict 准|不准|部分|未应 --note "实际发生"
  xuan bugua show <id> | xuan bugua list [--asker 用户]"""
import argparse, json, os, secrets, sys, uuid
from datetime import datetime, timezone, timedelta
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(D))
import config as C
os.makedirs(C.LOGS, exist_ok=True)
LOG = os.path.join(C.LOGS, 'bugua.jsonl')
H = json.load(open(os.path.join(D, 'hexagrams.json')))['hexagrams']
BY_BITS = {h['bits']: h for h in H}
TZ = timezone(timedelta(hours=8))
LIMIT = 3
TRI_DE = {'乾': '刚健', '坤': '柔顺', '震': '发动', '巽': '渗入', '坎': '险阻', '离': '光明', '艮': '停止', '兑': '喜悦'}
TRI_XIANG = {'乾': '天', '坤': '地', '震': '雷', '巽': '风', '坎': '水', '离': '火', '艮': '山', '兑': '泽'}
POS = ['初', '二', '三', '四', '五', '上']
STAGE = ['刚起步、还在底层', '基层负责', '中层', '高层、接近决策', '主事的人', '已经过头']

def load(): return [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
def save_all(rows):
    tmp = LOG + '.tmp'
    with open(tmp, 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, LOG)
def yao_key(i, yang): return ('初' if i == 0 else '上' if i == 5 else '') + ('九' if yang else '六') + ('' if i in (0, 5) else POS[i])
def reading(h, coins):
    up, lo = h['upper'], h['lower']
    nxt = next(x for x in H if x['number'] == h['number'] % 64 + 1)
    return {
        '卦': f"第{h['number']}卦 {h['full_name']}（上{up}{TRI_XIANG[up]} 下{lo}{TRI_XIANG[lo]}）",
        '内外卦': f"内卦（自身、根本）{lo}：{TRI_DE[lo]}；外卦（外部、处境）{up}：{TRI_DE[up]}",
        '卦辞': h['guaci'], '大象': h['daxiang'],
        '爻辞': [dict(位=POS[i] + '爻', 阶段=STAGE[i], 爻=k, 辞=h['yaoci'].get(k, '')) for i, k in ((i, yao_key(i, coins[i] == '1')) for i in range(6))],
        '顺序下一卦（照现在的路走下去的结果，推论用）': f"第{nxt['number']}卦 {nxt['full_name']}",
        '摘要': h['summary'],
        '解卦提示': '先看内外卦的性质对应所问之事，再按问事人所处阶段选一爻细读；结论说倾向和建议，不说绝对的吉凶。',
    }
def cast(a):
    now = datetime.now(TZ); rows = load()
    today = [r for r in rows if r['asker'] == a.asker and r['time'][:10] == now.strftime('%Y-%m-%d') and not r.get('test')]
    if not a.test and len(today) >= LIMIT:
        sys.exit(f"今天 {a.asker} 已经卜了 {len(today)} 卦（一天最多 3 卦）。明天再卜，或先回看今天的卦。")
    if a.coins:
        coins = a.coins.strip(); assert len(coins) == 6 and set(coins) <= {'0', '1'}, '--coins 需要 6 位 0/1，由下往上'
        src = 'user_physical'
    else:
        coins = ''.join(str(secrets.randbits(1)) for _ in range(6)); src = 'secrets'
    h = BY_BITS[coins]
    rec = dict(id=uuid.uuid4().hex[:8], time=now.isoformat(timespec='seconds'), asker=a.asker, question=a.q, coins=coins, coin_source=src,
               hexagram=h['number'], hexagram_name=h['full_name'], test=bool(a.test), feedback=None)
    with open(LOG, 'a') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(json.dumps(dict(record=rec, 今日已用=len(today) + (0 if a.test else 1), reading=reading(h, coins)), ensure_ascii=False, indent=1))
def feedback(a):
    rows = load(); hit = [r for r in rows if r['id'] == a.id]
    if not hit: sys.exit('找不到这一卦')
    hit[0]['feedback'] = dict(verdict=a.verdict, note=a.note, time=datetime.now(TZ).isoformat(timespec='seconds'))
    save_all(rows); print(json.dumps(hit[0], ensure_ascii=False))
def show(a):
    r = next((r for r in load() if r['id'] == a.id), None)
    if not r: sys.exit('找不到这一卦')
    print(json.dumps(dict(record=r, reading=reading(BY_BITS[r['coins']], r['coins'])), ensure_ascii=False, indent=1))
def lst(a):
    for r in load():
        if not a.asker or r['asker'] == a.asker:
            print(r['id'], r['time'], r['asker'], r['hexagram_name'], '[test]' if r.get('test') else '', r['question'][:40], '| 反馈:', (r['feedback'] or {}).get('verdict'))
p = argparse.ArgumentParser(prog='xuan bugua'); s = p.add_subparsers(dest='cmd', required=True)
c = s.add_parser('cast'); c.add_argument('--asker', required=True); c.add_argument('--q', required=True); c.add_argument('--coins'); c.add_argument('--test', action='store_true'); c.set_defaults(f=cast)
f = s.add_parser('feedback'); f.add_argument('id'); f.add_argument('--verdict', required=True, choices=['准', '不准', '部分', '未应']); f.add_argument('--note', default=''); f.set_defaults(f=feedback)
sh = s.add_parser('show'); sh.add_argument('id'); sh.set_defaults(f=show)
l = s.add_parser('list'); l.add_argument('--asker'); l.set_defaults(f=lst)
a = p.parse_args(); a.f(a)
