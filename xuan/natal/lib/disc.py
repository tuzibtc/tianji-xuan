"""（古籍格局属文学化表述…）免责行：关键推导块里出现 FLAG 中任一断语（按专题、前 40 字）即附加。
FLAG 表（disclaimer_flags.json）是可选文件，放在模型目录；公开版默认不带。"""
import json, re
import os
_FP = os.path.join(os.environ.get('XUAN_MODELS', ''), 'disclaimer_flags.json')
FLAG = {tuple(x) for x in json.load(open(_FP))} if os.path.exists(_FP) else set()   # 可选文件，公开版默认不带
DISC = '（古籍格局属文学化表述，不构成收入或成就预测）'
def key(a):
    a = re.sub(r'——《天纪》.*', '', a)
    if '〔倪师断法·应期〕' in a: return '应期:' + re.sub(r'当前大限\(.*?\)走【(.*?)】.*', r'\1', a.split('〕', 1)[1])
    return a[:40]
def fix_disc(text, topic):
    L = text.split('\n')
    try: h = next(i for i, l in enumerate(L) if l.startswith('**关键推导**'))
    except StopIteration: return text
    e = h + 1
    while e < len(L) and L[e].strip(): e += 1
    blk = [l for l in L[h + 1:e] if l != DISC]
    if any((topic, key(a)) in FLAG for a in blk if a.startswith('· ')): blk.append(DISC)
    return '\n'.join(L[:h + 1] + blk + L[e:])
