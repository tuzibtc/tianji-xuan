"""公开模式的输出过滤：去掉人名出处、集数、时间码、「出处」类段落，只留论断本身。
只作用于显示，不改动数据集或模型。"""
import re
MARK = re.compile(r'倪师|倪海厦|倪氏|天纪|第\s*\d+\s*集|\bp\d{2}\b|\d{1,2}:\d{2}(:\d{2})?|校勘|善本|出处|原文在|原话')
PAREN = re.compile(r'（[^（）]*）|\([^()]*\)')
DROP_LINE = re.compile(r'^\s*(· 〔[^〕]*〕|〔词义〕|（古籍格局属)')
BLOCK_START = ('**关键推导**', '**【经典出处】**', '▸ 《紫微斗数全书》卷二十二宫断语')
CJK = re.compile(r'[\u4e00-\u9fff]')
SECTION = re.compile(r'^(\*\*【|## |---\s*$|### )')

def _clauses(s):
    parts = re.split(r'(?<=[，、；：])', s)
    return ''.join(p for p in parts if not MARK.search(p)).rstrip('，、；：')

def clean_line(line):
    line = PAREN.sub(lambda m: '' if MARK.search(m.group(0)) else m.group(0), line)
    if not MARK.search(line): return line
    out = []
    for sent in re.split(r'(?<=[。！？])', line):
        if not MARK.search(sent): out.append(sent); continue
        if '「' in sent or '“' in sent: continue          # 带引号的原话：整句去掉
        c = _clauses(sent)
        if c and not MARK.search(c):
            out.append(c + ('。' if sent.endswith('。') and not c.endswith('。') else ''))
    s = ''.join(out)
    return None if (not s.strip() or MARK.search(s) or s.strip() in ('·', '-', '✦', '◇')) else s

def clean_text(text):
    L = text.split('\n'); out = []; skip = False
    for ln in L:
        if ln.startswith(BLOCK_START): skip = True; continue
        if skip:
            if SECTION.match(ln) and not ln.startswith(BLOCK_START): skip = False
            else: continue
        if DROP_LINE.match(ln): continue
        c = clean_line(ln)
        if c is None: continue
        out.append(c)
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip('\n')

def clean_obj(o):
    """JSON 输出：去掉 src / cite / 出处 字段，字符串逐行清洗。"""
    if isinstance(o, dict):
        return {k: clean_obj(v) for k, v in o.items() if k not in ('src', 'cite', '出处', '_src')}
    if isinstance(o, list): return [clean_obj(x) for x in o]
    if isinstance(o, str):
        return clean_text(o) if CJK.search(o) else o   # 时间戳、id 等不动
    return o
