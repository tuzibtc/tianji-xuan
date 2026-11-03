"""〔词义〕行渲染：由 关键推导 块内出现的术语（按首现位置、最多 5 个）+ 按专题的释义词典生成。
词典（glossary.json）是可选文件，放在模型目录；公开版默认不带。"""
import json, re
import os
_GP = os.path.join(os.environ.get('XUAN_MODELS', ''), 'glossary.json')
G = json.load(open(_GP)) if os.path.exists(_GP) else None   # 可选：没有就不加〔词义〕行
def strip_gloss(text):
    return '\n'.join(l for l in text.split('\n') if not l.startswith('〔词义〕'))
def gloss_line(block, topic):
    if G is None: return None
    pos = {x: min([block.find(k) for k in G['KW'][x] if k in block] or [-1]) for x in G['ORDER']}
    names = [x for x in sorted(G['ORDER'], key=lambda x: pos[x]) if pos[x] >= 0][:G['MAX']]
    if not names: return None
    return '〔词义〕' + '；'.join(n + '：' + G['defs'][n].get(topic, next(iter(G['defs'][n].values()))) for n in names)
def add_gloss(text, topic):
    L = text.split('\n')
    try: h = next(i for i, l in enumerate(L) if l.startswith('**关键推导**'))
    except StopIteration: return text
    e = h + 1
    while e < len(L) and L[e].strip(): e += 1
    blk = L[h + 1:e]
    ins = e
    if blk and blk[-1].startswith('（古籍格局属'): ins = e - 1; blk = blk[:-1]
    g = gloss_line('\n'.join(blk), topic)
    if g: L.insert(ins, g)
    return '\n'.join(L)
