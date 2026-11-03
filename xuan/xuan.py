"""xuan —— 《天纪》紫微斗数统一入口：排盘 · 本命 13 维 · 流年流月大限 · 合盘 · 卜卦 · 阳宅 · 相法 · 测字 · 反馈校准。
第一次使用先运行 `xuan setup`（克隆上游引擎、安装依赖、下载并校验解读数据集）。
公开模式（默认，XUAN_PUBLIC=1）：不显示置信标签，过滤出处与时间码，每个结论末尾加「仅供参考」。
设 XUAN_PUBLIC=0 可显示内部置信标签（开发调试用）。"""
import argparse, json, os, re, subprocess, sys
N = os.path.dirname(os.path.abspath(__file__))
for p in (N, f'{N}/natal', f'{N}/natal/lib', f'{N}/yunxian'):
    sys.path.insert(0, p)
import config as C
import feedback as FB
import sanitize as SZ
from project import PROJECT, VERSION, FOOTER
BR = '子丑寅卯辰巳午未申酉戌亥'; STEM = '甲乙丙丁戊己庚辛壬癸'
L_OFF, L_REB, L_INF, L_TING = '【官方原文】', '【自建库】', '【推论·不做数】', '【只能听听】'
TOPIC_ZH = {'overall': '整体', 'wealth': '财运', 'career': '事业', 'love': '感情', 'health': '健康', 'siblings': '兄弟', 'children': '子女'}

def die(msg): sys.stderr.write(msg.rstrip() + '\n'); sys.exit(2)
def lab(x): return '' if C.PUBLIC else x
def out_text(text):
    sys.stdout.write(text.rstrip() + ('\n\n' + FOOTER if C.PUBLIC else '') + '\n')
def out_json(obj):
    if C.PUBLIC and isinstance(obj, dict): obj = {**SZ.clean_obj(obj), '提示': FOOTER}
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')
def need_engine():
    if not os.path.exists(C.TSX): die(f'还没安装引擎：请先运行 `xuan setup`（数据目录 {C.HOME}）')

# ---------- 人物与时辰 ----------
def people():
    if not os.path.exists(C.PEOPLE): return {}
    return {p['id']: p for p in json.load(open(C.PEOPLE))}
def tsx(script, args=(), stdin=None):
    need_engine()
    r = subprocess.run([C.TSX, script, *map(str, args)], input=stdin, capture_output=True, text=True, cwd=C.ENGINE, env=C.env())
    if r.returncode: die(r.stderr[-2000:])
    return r.stdout
def resolve(a, prefix=''):
    """时辰优先级：--hour > 钟表时间（经引擎换算真太阳时）> 人物库里暂定的 hour_index。"""
    g = lambda k: getattr(a, prefix + k, None)
    pid, hour, date, gender, clock, lon = g('person'), g('hour'), g('date'), g('gender'), g('clock'), g('lon')
    p = None; notes = []; uncertain = False; meta = None
    if pid:
        ppl = people()
        if pid not in ppl: die(f'人物库（{C.PEOPLE}）里没有 id={pid}；现有：{", ".join(ppl) or "（空）"}')
        p = ppl[pid]; date = p.get('date'); gender = p['gender']
        if lon is None: lon = p.get('lon')
        if clock is None and re.fullmatch(r'\d{1,2}:\d{2}', p.get('clock_time') or ''): clock = p['clock_time']
    if not date or gender not in ('male', 'female'): die('需要 --person <id>，或 --date YYYY-MM-DD --gender male|female')
    y, m, d = map(int, date.split('-'))
    if hour is not None:
        notes.append(f'时辰按指定：{BR[hour]}时')
    elif clock:
        hh, mm = map(int, clock.split(':'))
        meta = json.loads(tsx(f'{N}/natal/hour_index.ts', [y, m, d, hh, mm] + ([lon] if lon is not None else [])).strip().splitlines()[-1])
        cd = meta['chartDate']; y, m, d, hour = cd['year'], cd['month'], cd['day'], meta['hourIndex']
        notes.append(f"钟表 {clock} → 北京时 {meta['beijingStandard']}{'（已扣夏令时）' if meta['chinaDST'] else ''} → 真太阳时 {meta['trueSolar']} → {BR[hour]}时")
    elif p and p.get('hour_index') is not None:
        hour = p['hour_index']; uncertain = True
        notes.append(f"出生时间不确定，暂用 {BR[hour]}时，结论只能参考")
    else:
        die(f"{(p or {}).get('name', '')} 没有可用的出生时间，请用 --{prefix.replace('_', '-')}hour 0-11 指定（子=0 … 亥=11）或 --{prefix.replace('_', '-')}clock HH:MM")
    if p and g('hour') is not None and not re.fullmatch(r'\d{1,2}:\d{2}', p.get('clock_time') or ''):
        uncertain = True; notes.append('出生时间还没定，这是按候选时辰看的，结论只能参考')
    return dict(y=y, m=m, d=d, hour=hour, gender=gender, lon=lon, key=f'{y}-{m:02d}-{d:02d}-{hour}-{gender}', person=p, notes=notes, uncertain=uncertain, meta=meta)
def head(label, R, extra=''):
    who = f"{R['person']['name']}" if R['person'] else R['key']
    lb = lab(label + (L_TING if R['uncertain'] and label != L_TING else ''))
    return f"{lb}{' ' if lb else ''}{who} · 盘 {R['key']}{extra}\n" + ''.join(f'  · {n}\n' for n in R['notes'])

# ---------- chart ----------
def cmd_chart(a):
    R = resolve(a); f = json.loads(tsx(f'{N}/natal/features.ts', stdin=R['key'] + '\n').strip().splitlines()[-1])
    if a.json: return out_json(dict(**{k: R[k] for k in ('key', 'notes', 'uncertain')}, chart=f))
    L = [head(L_REB, R, '（引擎排盘，亮度流派 XD2）'),
         f"命宫 {BR[f['mg']]}  身宫 {BR[f['sg']]}  {f['ju']}  命主 {f['mz']}  身主 {f['sz']}  生年 {STEM[f['ys']]}{BR[f['yb']]}  {f['yyg']}"]
    for P in sorted(f['P'], key=lambda x: x['b']):
        st = sorted(P['st'], key=lambda s: s[1] != 'major')
        s = ' '.join(f"{n}{('(' + braw + ')') if braw else ''}{('化' + h) if h else ''}" for n, t, braw, b, h in st)
        L.append(f"{STEM[P['s']]}{BR[P['b']]} {P['n']}{'·身' if P['shen'] else ''}{'·空宫' if P['empty'] else ''}：{s}" + (f"  自化 {' '.join(P['self'])}" if P['self'] else ''))
    L.append('大限：' + '  '.join(f'{s}-{e}{BR[b]}' for s, e, b in f['dx']))
    out_text('\n'.join(L))

# ---------- natal ----------
def cmd_natal(a):
    import lookup, chartfeat
    from natal import reading as RD
    R = resolve(a); topics = a.topics.split(',') if a.topics else list(lookup.LBL)
    bad = [t for t in topics if t not in lookup.LBL]
    if bad: die('未知专题：' + ','.join(bad) + '；可选：' + ','.join(lookup.LBL))
    src = a.source; off = None
    if src in ('auto', 'official') and 1950 <= R['y'] <= 2026:
        if not lookup.available(R['y']): die(f'本机还没有 {R["y"]} 年的解读数据：请运行 `xuan setup`')
        off = lookup.find(R['y'], R['m'], R['d'], R['hour'], R['gender'])
    if src == 'official' and not off: die('解读数据集里没有这张盘（只覆盖 1950–2026 年出生）')
    cmp = None
    if off and src != 'rebuilt':
        label = L_OFF; res = {t: off['c'][t] for t in topics}; srcnote = '紫微斗数开源解读数据集 v4.0（本命视图，当前大限按 2026 年生成）'
    else:
        if not RD.have_models(topics): die('这张盘不在数据集覆盖范围（1950–2026）内，需要自建论断库：请先运行 `xuan train`（需要较大内存和较长时间）')
        chartfeat.GEN_YEAR = a.asof
        res = RD.reading(RD.features(R['key']), topics); label = L_REB; srcnote = f'自建论断库（由本机数据集训练），当前大限按 {a.asof} 年算'
    if a.compare:
        chartfeat.GEN_YEAR = a.asof
        if not RD.have_models(topics): die('对照需要自建论断库：请先运行 `xuan train`')
        cmp = RD.compare(R['key'], RD.reading(RD.features(R['key']), topics))
    if C.PUBLIC: res = {t: SZ.clean_text(x) for t, x in res.items()}
    if a.json: return out_json(dict(key=R['key'], notes=R['notes'], c=res, compare=cmp, **({} if C.PUBLIC else dict(label=label, source=srcnote))))
    L = [head(label, R)] + ([] if C.PUBLIC else [f'来源：{srcnote}\n'])
    if cmp is not None:
        L.append('## 自建库 vs 数据集原文 逐专题对照')
        L += [f"{x['topic']:12s} 逐字一致={'是' if x['exact'] else '否'} P={x['P']:.4f} R={x['R']:.4f}" for x in cmp]
    for t in topics: L.append(f'\n---\n## {lookup.LBL.get(t, t)}\n\n{res[t]}')
    out_text('\n'.join(L))

# ---------- 运限 ----------
def ychart(R):
    import engine as E
    k = f"{R['person']['id'] if R['person'] else R['key']}_h{R['hour']}"
    if k not in E.CH:
        E.CH[k] = json.loads(tsx(f'{N}/yunxian/dump_one.ts', stdin=json.dumps(dict(key=k, y=R['y'], m=R['m'], d=R['d'], gender=R['gender'], lon=R['lon'] or 116.4, hour=R['hour']))))
    return k, E.CH[k]
def pct(vals, v): return round(100 * sum(x <= v for x in vals) / len(vals))
def cmd_yun(a, kind):
    import engine as E
    R = resolve(a); k, c = ychart(R); ly = c['lunar']['lunarYear']
    if kind == 'month':
        if not 1 <= a.month <= 12: die('--month 是农历月 1–12')
        r = E.reading(c, 'month', a.year, a.month); pool = [E.reading(c, 'month', a.year, mm)['score'] for mm in range(1, 13)]; scope = f'{a.year} 年 12 个农历月'
        title = f'{a.year} 年农历 {a.month} 月（斗君起流月）'
    elif kind == 'decade':
        r = E.reading(c, 'decade', a.year); pool = [E.reading(c, 'decade', ly + x['s'] - 1)['score'] for x in c['daxians']]; scope = '一生各个大限'
        title = f"{a.year} 年所在大限 {r.get('range', '')}"
    else:
        r = E.reading(c, 'year', a.year); pool = [E.reading(c, 'year', ly + i)['score'] for i in range(100)]; scope = '一生虚岁 1–100 岁各年'
        title = f'{a.year} 年（虚岁 {E.xusui(c, a.year)}，小限流年）'
    P = {t: pct([x[t] for x in pool], v) for t, v in r['score'].items()}
    caution = '运限分数只能排先后，不报吉凶，只看这一段在本人一生里的相对位置。'
    res = dict(palace=r['palace'], decade_palace=r.get('decade_palace'), focus=r.get('focus'), score=r['score'], percentile=P, percentile_scope=scope, notes=R['notes'], caution=caution)
    if a.raw: res['facts'] = r['facts']
    if a.json: return out_json(res)
    L = [head(L_TING, R, f' · {title}'), f"走到：{r['palace']}" + (f"；大限在 {r['decade_palace']}" if r.get('decade_palace') else '') + (f"；重点在「{r['focus']}」" if r.get('focus') else ''),
         f'相对位置（在{scope}里，100=最好）：' + '、'.join(f'{TOPIC_ZH[t]} {P[t]}' for t in r['score']), '说明：' + caution]
    if a.raw: L.append('触发规则：\n' + '\n'.join(f'   {f}' for f in r['facts'] if f[4]))
    out_text('\n'.join(L))

# ---------- 合盘 ----------
def cmd_hepan(a):
    sys.path.insert(0, f'{N}/hepan'); import hepan as H
    RA, RB = resolve(a, 'a_'), resolve(a, 'b_')
    ka, _ = ychart(RA); kb, _ = ychart(RB)
    r = H.hepan(ka, kb, a.year)
    res = dict(a=ka, b=kb, notes=RA['notes'] + RB['notes'], **r, caution='合盘规则没有用真实成对样本验证过，只看倾向。')
    if a.json: return out_json(res)
    L = [f"{lab(L_INF)}合盘 A={RA['person']['name'] if RA['person'] else ka} × B={RB['person']['name'] if RB['person'] else kb}（{a.year} 年）", *[f'  · {n}' for n in res['notes']],
         f"总分 {r['total']}，{r['stars']} 星", '理由：', *[f'   {rid} {v:+} {t}' for rid, v, t in r['reasons']], '说明：' + res['caution']]
    out_text('\n'.join(L))

# ---------- 卜卦 / 风水（调用子脚本） ----------
def passthrough(script, args, label):
    r = subprocess.run([C.PY, script, *args], capture_output=True, text=True, env=C.env())
    if r.returncode: sys.stderr.write(r.stderr); sys.stdout.write(r.stdout); sys.exit(r.returncode)
    try:
        o = json.loads(r.stdout)
        if isinstance(o, dict) and not C.PUBLIC: o = {'置信': label, **o}
        out_json(o)
    except json.JSONDecodeError:
        out_text(r.stdout)
def calib_hint(m):
    if m not in C.CALIB_METHODS: return
    s = next(x for x in FB.status() if x['method'] == m)
    msg = f"[校准] {m}：上次复盘后新增有效反馈 {s['new_since_calibration']}/{FB.TRIGGER}"
    if s['need_review']: msg += ' —— 够量了，该复盘校准了（复盘完用 xuan calib-mark 记一笔）'
    sys.stderr.write(msg + '\n')

# ---------- 相法 / 测字 ----------
def cmd_rules(a, m):
    R = json.load(open(f'{N}/{m}/rules.json'))
    if m == 'xiangfa' and a.part != 'all':
        keep = {'face': ('_note', 'face_palaces', 'face_rules', 'inputs'), 'palm': ('_note', 'palm_rules', 'inputs')}[a.part]
        R = {k: v for k, v in R.items() if k in keep}
    out_json(R if C.PUBLIC else {'置信': L_INF, **R})

# ---------- 日志 / 校准 ----------
def cmd_log(a):
    if a.sub == 'add':
        if a.method == 'bugua': die('卜卦用 xuan bugua cast，会自动记日志')
        args = [a.method, 'add', '--asker', a.asker, '--input', a.input, '--summary', a.summary, '--rules', a.rules] + (['--test'] if a.test else [])
        subprocess.run([C.PY, f'{N}/common/readlog.py', *args], check=True, env=C.env())
    elif a.sub == 'feedback':
        m, r = FB.find_id(a.id)
        if not m: die(f'所有日志里都找不到 id={a.id}')
        if m == 'bugua': subprocess.run([C.PY, f'{N}/bugua/bugua.py', 'feedback', a.id, '--verdict', a.verdict, '--note', a.note], check=True, env=C.env())
        else: subprocess.run([C.PY, f'{N}/common/readlog.py', m, 'feedback', a.id, '--verdict', a.verdict, '--note', a.note], check=True, env=C.env())
        calib_hint(m)
    else:
        for m in ([a.method] if a.method else C.LOG_METHODS):
            for r in FB.load(m):
                fb = (r.get('feedback') or {}).get('verdict')
                print(m, r['id'], r['time'], r['asker'], '[test]' if r.get('test') else '', (r.get('question') or r.get('summary') or '')[:40], '| 反馈:', fb)
def cmd_calib(a):
    rows = FB.status()
    if a.json: return sys.stdout.write(json.dumps(dict(rows=rows, all_passed=all(r['passed'] for r in rows)), ensure_ascii=False, indent=1) + '\n')
    L = ['校准状态（统计，不是论断）。记分：准1 / 部分0.5 / 不准0，未应和试跑不计。', f'规则：上次复盘后新增 ≥{FB.TRIGGER} 条 → 复盘；上次改规则后 ≥{FB.PASS_N} 条且准确率 ≥{int(FB.PASS_ACC * 100)}% → 过关。']
    for r in rows:
        acc = '—' if r['accuracy'] is None else f"{r['accuracy'] * 100:.1f}%"
        L.append(f"{r['method']:9s} 新增 {r['new_since_calibration']:3d}/{FB.TRIGGER}{' ←该复盘' if r['need_review'] else ''}  改规则后 {r['since_rule_change']:3d} 条 准确率 {acc}{'  ✔过关' if r['passed'] else ''}")
    L.append('全部过关，校准结束。' if all(r['passed'] for r in rows) else '尚未全部过关。')
    print('\n'.join(L))
def cmd_calib_mark(a):
    print(json.dumps(FB.mark(a.method, a.rule_changed, a.note), ensure_ascii=False))

# ---------- 安装 / 训练 / 信息 ----------
def cmd_setup(a):
    import setup_engine; setup_engine.main(a)
def cmd_train(a):
    import train; train.main(a)
def cmd_info(a):
    d = dict(project=PROJECT, version=VERSION, home=C.HOME, public=C.PUBLIC, engine=os.path.exists(C.TSX),
             dataset_years=len([f for f in os.listdir(C.DATASET) if f.endswith('.zst')]) if os.path.isdir(C.DATASET) else 0,
             models=sorted(f[:-4] for f in os.listdir(C.MODELS) if f.endswith('.pkl')) if os.path.isdir(C.MODELS) else [], people=C.PEOPLE)
    print(json.dumps(d, ensure_ascii=False, indent=1))

def person_args(p, prefix=''):
    o = '--' + prefix.replace('_', '-')
    p.add_argument(o + 'person', dest=prefix + 'person', help='人物库 people.json 里的 id'); p.add_argument(o + 'hour', dest=prefix + 'hour', type=int, help='时辰序 0–11（子=0…亥=11）')
    p.add_argument(o + 'date', dest=prefix + 'date', help='公历生日 YYYY-MM-DD'); p.add_argument(o + 'gender', dest=prefix + 'gender', choices=['male', 'female'])
    p.add_argument(o + 'clock', dest=prefix + 'clock', help='出生钟表时间 HH:MM'); p.add_argument(o + 'lon', dest=prefix + 'lon', type=float, help='出生地经度')
def main():
    argv = sys.argv[1:]
    if argv and argv[0] == 'bugua':
        r = passthrough(f'{N}/bugua/bugua.py', argv[1:], L_INF)
        if len(argv) > 1 and argv[1] == 'feedback': calib_hint('bugua')
        return r
    if argv and argv[0] == 'fengshui': return passthrough(f'{N}/fengshui/yangzhai.py', argv[1:], L_INF)
    ap = argparse.ArgumentParser(prog='xuan', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('setup', help='安装：克隆固定版本的上游引擎、npm 安装、下载并校验解读数据集 v4.0')
    c.add_argument('--no-dataset', action='store_true'); c.add_argument('--years', help='只下载部分年份，例如 1980-1999'); c.add_argument('--force', action='store_true'); c.set_defaults(f=cmd_setup)
    c = s.add_parser('train', help='可选：用本机数据集训练自建论断库（覆盖 1950 年前 / 2027 年后出生的人）')
    c.add_argument('--topics'); c.add_argument('--ntrain', type=int, default=60000); c.add_argument('--ntest', type=int, default=20000); c.add_argument('--per-year', type=int, default=1100)
    c.add_argument('--jobs', type=int, default=2); c.set_defaults(f=cmd_train)
    c = s.add_parser('info', help='显示安装状态'); c.set_defaults(f=cmd_info)
    s.add_parser('bugua', help='卜卦：xuan bugua cast|feedback|show|list …')
    s.add_parser('fengshui', help="阳宅：xuan fengshui --rooms '{…}' --people '{…}'")
    c = s.add_parser('chart', help='排盘'); person_args(c); c.add_argument('--json', action='store_true'); c.set_defaults(f=cmd_chart)
    c = s.add_parser('natal', help='本命 13 维'); person_args(c)
    c.add_argument('--topics'); c.add_argument('--source', choices=['auto', 'official', 'rebuilt'], default='auto')
    c.add_argument('--compare', action='store_true', help='自建库与数据集原文逐专题对照'); c.add_argument('--asof', type=int, default=2026); c.add_argument('--json', action='store_true'); c.set_defaults(f=cmd_natal)
    for name, kind, hp in (('year', 'year', '流年（小限）'), ('month', 'month', '流月（斗君）'), ('decade', 'decade', '大限')):
        c = s.add_parser(name, help=hp + '，只报一生里的相对位置'); person_args(c); c.add_argument('--year', type=int, required=True)
        if kind == 'month': c.add_argument('--month', type=int, required=True, help='农历月 1–12')
        c.add_argument('--raw', action='store_true'); c.add_argument('--json', action='store_true'); c.set_defaults(f=lambda a, k=kind: cmd_yun(a, k))
    c = s.add_parser('hepan', help='合盘（未验证）'); person_args(c, 'a_'); person_args(c, 'b_')
    c.add_argument('--a', dest='a_person'); c.add_argument('--b', dest='b_person'); c.add_argument('--year', type=int, default=2026); c.add_argument('--json', action='store_true'); c.set_defaults(f=cmd_hepan)
    c = s.add_parser('xiang', help='相法规则表（面相 / 手相）'); c.add_argument('--part', choices=['face', 'palm', 'all'], default='all'); c.set_defaults(f=lambda a: cmd_rules(a, 'xiangfa'))
    c = s.add_parser('cezi', help='测字规则表（六神）'); c.set_defaults(f=lambda a: cmd_rules(a, 'cezi'))
    c = s.add_parser('log', help='解读日志：add / feedback / list'); ls = c.add_subparsers(dest='sub', required=True)
    x = ls.add_parser('add'); x.add_argument('--method', required=True, choices=C.LOG_METHODS); x.add_argument('--asker', required=True)
    x.add_argument('--input', required=True); x.add_argument('--summary', required=True); x.add_argument('--rules', default=''); x.add_argument('--test', action='store_true')
    x = ls.add_parser('feedback'); x.add_argument('id'); x.add_argument('--verdict', required=True, choices=['准', '不准', '部分', '未应']); x.add_argument('--note', default='')
    x = ls.add_parser('list'); x.add_argument('--method', choices=C.LOG_METHODS)
    c.set_defaults(f=cmd_log)
    c = s.add_parser('calib-status', help='各方法校准进度'); c.add_argument('--json', action='store_true'); c.set_defaults(f=cmd_calib)
    c = s.add_parser('calib-mark', help='复盘完记一笔（--rule-changed 表示改了规则）')
    c.add_argument('--method', required=True, choices=C.CALIB_METHODS); c.add_argument('--rule-changed', action='store_true'); c.add_argument('--note', default=''); c.set_defaults(f=cmd_calib_mark)
    a = ap.parse_args(argv)
    if a.cmd == 'hepan' and not ((a.a_person or a.a_date) and (a.b_person or a.b_date)): die('合盘需要 --a <id> --b <id>（或 --a-date / --b-date 等）')
    os.makedirs(C.HOME, exist_ok=True); os.makedirs(C.LOGS, exist_ok=True)
    a.f(a)
if __name__ == '__main__': main()
