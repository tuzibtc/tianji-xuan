"""把一维解读文本解析成 (gap, section, template) 序列；模板化 = 用盘面派生串替换动态片段。"""
import re
DYN_PREFIX = ('◆', '▍', '*你的', '本宫主星', '▸ **本盘合参', '你的身宫落', '  （空宫', '**大限走到', '· 〔倪师断法·应期〕', '同宫第二主星', '· 〔倪师断法·紫微解厄〕', '· 〔倪师断法·化忌对冲〕',
              '· 〔倪师断法·疾厄真法〕', '全盘杀星相对最集中在', '杀星分散在', '⭐ **天马落空**')
HDR = re.compile(r'^(\*\*【[^】]+】\*\*|## |### |▍)')
class Seen(dict):
    pass
# 行类型 → 只允许的派生 key 前缀（避免同值串被别的 key 抢走，导致模板碎片化）
PREFIX_KEYS = {'**大限走到': ('DXR1', 'DXR2', 'DXH'), '· 〔倪师断法·紫微解厄〕': ('J:',), '· 〔倪师断法·化忌对冲〕': ('HJ:',),
               '*你的': ('A:', 'M1:'),
               '· 〔倪师断法·疾厄真法〕': ('WPX', 'WSPL', 'HJX'), '全盘杀星相对最集中在': ('WPXB',), '杀星分散在': ('WSPLB',), '⭐ **天马落空**': ('TMK',), '· 〔倪师断法·应期〕': ('YQ',)}
def _mk(items):
    seen = {}; alts = []
    for k, v in items:
        if v in seen: continue
        seen[v] = k; alts.append(re.escape(v))
    return (re.compile('|'.join(alts)) if alts else None), seen
def build_sub(derived, order):
    """order: 派生 key 的优先序列；返回 (regex, inv) 。"""
    items = [(k, v) for k, v in derived.items() if v and (len(v) >= 2 or k.startswith('SF:'))]
    pri = {k: i for i, k in enumerate(order)}
    items.sort(key=lambda kv: (-len(kv[1]), pri.get(kv[0], 999)))
    rx, sd = _mk(items); seen = Seen(sd); seen.items_ = items; seen.cache = {}
    return rx, seen
def templatize(line, rx, seen):
    if rx is None or not line.startswith(DYN_PREFIX): return line
    for pf, ks in PREFIX_KEYS.items():
        if line.startswith(pf) and hasattr(seen, 'items_'):
            if pf not in seen.cache: seen.cache[pf] = _mk([kv for kv in seen.items_ if kv[0].startswith(ks)])
            r2, s2 = seen.cache[pf]
            return line if r2 is None else r2.sub(lambda m: '{' + s2[m.group(0)] + '}', line)
    return rx.sub(lambda m: '{' + seen[m.group(0)] + '}', line)
def render(tpl, derived):
    if '{' not in tpl: return tpl
    return re.sub(r'\{([A-Z0-9]+(?::[^}]+)?)\}', lambda m: derived.get(m.group(1), m.group(0)), tpl)
HEADERLIKE = ('---', '*你的', '> ', '**关键推导**', '▸ 《紫微斗数全书》卷二十二宫断语')
SECSTART = ('**关键推导**', '▸ 《紫微斗数全书》卷二十二宫断语')
def starts_section(tpl):
    return bool(HDR.match(tpl)) or tpl.startswith(SECSTART)
def is_header(tpl):
    return bool(HDR.match(tpl)) or tpl.startswith(HEADERLIKE)
def section_key(tpl):
    if tpl.startswith('▍'):
        return tpl.split('**：')[0]
    return tpl
def parse(text, rx, seen):
    """返回 [(gap, sec, tpl, occ, dsec)], tail
    sec  : 单元身份用的粗段（▍ / ## 段内的行带段名；顶层段行不带）
    dsec : 依附判断用的细段（最近一个标题类行）"""
    out = []; gap = 0; sec = ''; dsec = ''; occ = {}
    for ln in text.split('\n'):
        if ln == '': gap += 1; continue
        tpl = templatize(ln, rx, seen)
        if ln.startswith('   ') and gap == 0 and out and not out[-1][2].startswith('---'):
            out[-1][2] += '\n' + tpl; continue
        if tpl.startswith('▍') or tpl.startswith('## '): sec = section_key(tpl)
        elif tpl.startswith('**【'): sec = ''
        elif tpl.startswith('▸ 《紫微斗数全书》卷二十二宫断语'): sec = '▸Q'
        if starts_section(tpl): dsec = section_key(tpl)
        key = (sec, tpl); occ[key] = occ.get(key, 0) + 1
        out.append([gap, sec, tpl, occ[key], dsec]); gap = 0
    for i, it in enumerate(out):
        if it[2] == '---':
            nxt = next((x for x in out[i + 1:] if x[2] != '---'), None)
            it[4] = '>' + (nxt[2] if nxt else 'END'); it[1] = it[4]; it[3] = 1
    return [tuple(x) for x in out], gap
