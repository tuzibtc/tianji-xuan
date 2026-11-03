#!/usr/bin/env python3
"""通用解读日志（风水 / 相法 / 测字 / 运限 / 合盘 / 本命）：每次解读记一条，事后回填反馈用于校准。
  xuan log add --method fengshui --asker 用户 --input "输入摘要" --summary "结论" [--rules Y02,Y11] [--test]
  xuan log feedback <id> --verdict 准|不准|部分|未应 --note "实际"
日志写到 XUAN_HOME/logs/<method>.jsonl"""
import argparse, json, os, sys, uuid
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
TZ = timezone(timedelta(hours=8))
p = argparse.ArgumentParser(); p.add_argument('skill'); s = p.add_subparsers(dest='cmd', required=True)
a = s.add_parser('add'); a.add_argument('--asker', required=True); a.add_argument('--input', required=True); a.add_argument('--summary', required=True); a.add_argument('--rules', default=''); a.add_argument('--test', action='store_true')
f = s.add_parser('feedback'); f.add_argument('id'); f.add_argument('--verdict', required=True, choices=['准', '不准', '部分', '未应']); f.add_argument('--note', default='')
s.add_parser('list')
x = p.parse_args()
assert x.skill in ('fengshui', 'xiangfa', 'cezi', 'yunxian', 'hepan', 'natal'), '未知方法'
os.makedirs(C.LOGS, exist_ok=True)
LOG = os.path.join(C.LOGS, f'{x.skill}.jsonl')
rows = [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
now = datetime.now(TZ).isoformat(timespec='seconds')
if x.cmd == 'add':
    r = dict(id=uuid.uuid4().hex[:8], time=now, skill=x.skill, asker=x.asker, input=x.input, summary=x.summary, rules=[t for t in x.rules.split(',') if t], test=x.test, feedback=None)
    open(LOG, 'a').write(json.dumps(r, ensure_ascii=False) + '\n'); print(json.dumps(r, ensure_ascii=False))
elif x.cmd == 'feedback':
    hit = [r for r in rows if r['id'] == x.id]
    if not hit: sys.exit('找不到该条')
    hit[0]['feedback'] = dict(verdict=x.verdict, note=x.note, time=now)
    tmp = LOG + '.tmp'; open(tmp, 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)); os.replace(tmp, LOG)
    print(json.dumps(hit[0], ensure_ascii=False))
else:
    for r in rows: print(r['id'], r['time'], r['asker'], '[test]' if r['test'] else '', r['summary'][:50], '| 反馈:', (r['feedback'] or {}).get('verdict'))
