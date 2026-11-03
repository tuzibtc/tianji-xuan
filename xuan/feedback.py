"""共用反馈 / 日志层：读各方法日志、按 id 回填反馈、统计校准状态。
记分：准=1、部分=0.5、不准=0；未应不计；test 记录不计。
复盘触发：上次复盘之后新增 ≥30 条有效反馈。
过关：上次改规则之后 ≥100 条有效反馈且准确率 ≥90%。五种方法都过关 → 校准结束。"""
import json, os, subprocess
from datetime import datetime, timezone, timedelta
import config as C
TZ = timezone(timedelta(hours=8))
SCORE = {'准': 1.0, '部分': 0.5, '不准': 0.0}
TRIGGER, PASS_N, PASS_ACC = 30, 100, 0.90

def log_path(m): return os.path.join(C.LOGS, f'{m}.jsonl')
def load(m):
    p = log_path(m)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
def find_id(rid):
    for m in C.LOG_METHODS:
        for r in load(m):
            if r['id'] == rid: return m, r
    return None, None

def state():
    s = json.load(open(C.CALIB)) if os.path.exists(C.CALIB) else {}
    for m in C.CALIB_METHODS: s.setdefault(m, dict(last_calibration=None, last_rule_change=None, history=[]))
    return s
def save_state(s):
    tmp = C.CALIB + '.tmp'; json.dump(s, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, C.CALIB)

def scored(m, since=None):
    out = []
    for r in load(m):
        fb = r.get('feedback') or {}
        if r.get('test') or fb.get('verdict') not in SCORE: continue
        if since and fb.get('time', '') <= since: continue
        out.append(SCORE[fb['verdict']])
    return out

def status():
    s = state(); rows = []
    for m in C.CALIB_METHODS:
        st = s[m]; new = scored(m, st['last_calibration']); base = scored(m, st['last_rule_change'])
        acc = sum(base) / len(base) if base else None
        rows.append(dict(method=m, new_since_calibration=len(new), need_review=len(new) >= TRIGGER,
                         since_rule_change=len(base), accuracy=acc, passed=len(base) >= PASS_N and acc is not None and acc >= PASS_ACC,
                         last_calibration=st['last_calibration'], last_rule_change=st['last_rule_change']))
    return rows

def mark(m, rule_changed, note):
    s = state(); now = datetime.now(TZ).isoformat(timespec='seconds')
    n_new = len(scored(m, s[m]['last_calibration']))
    s[m]['last_calibration'] = now
    if rule_changed: s[m]['last_rule_change'] = now
    s[m]['history'].append(dict(time=now, rule_changed=rule_changed, note=note, n_new=n_new))
    save_state(s); return s[m]
