"""合盘（交往 / 合作）：只用双方本命盘与生年四化，按事先设定的规则加减分；没有成对真实样本验证过。
python3 hepan.py 由 xuan hepan 调用。"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'yunxian'))
from engine import CH, pal, view, reading, SIX_SHA
SIHUA = {'甲': '廉贞 破军 武曲 太阳', '乙': '天机 天梁 紫微 太阴', '丙': '天同 天机 文昌 廉贞', '丁': '太阴 天同 天机 巨门',
         '戊': '贪狼 太阴 右弼 天机', '己': '武曲 贪狼 天梁 文曲', '庚': '太阳 武曲 太阴 天同', '辛': '巨门 太阳 文曲 文昌',
         '壬': '天梁 紫微 左辅 武曲', '癸': '破军 巨门 太阴 贪狼'}
RULES = {
 'H1': dict(w=1.5, text='一方夫妻宫主星=对方命宫主星'),
 'H2': dict(w=None, text='婚姻必须夫妻宫+福德宫并看；福德宫烂夫妻要散'),
 'H3': dict(w=-2.0, text='夫妻/福德见廉破、廉贪或化忌：生离死别之象'),
 'H4': dict(w=-1.5, text='男命太阴化忌、女命太阳化忌：配偶多灾/婚姻反复'),
 'H5': dict(w=-1.0, text='男命娶七杀入命之妻：很累，草木皆兵'),
 'H6': dict(w=-1.0, text='双方命宫皆杀破狼'),
 'H7': dict(w=-1.0, text='生肖对冲者相克'),
 'H8': dict(w=None, text='A 生年禄入 B 命/财/夫 +1；A 生年忌入 B 命 -1.5、入 B 夫妻 -2'),
 'H9': dict(w=1.0, text='男命命宫红鸾必招美妻，女命红鸾必有贵夫'),
 'H10': dict(w=None, text='当年两人所在大限的感情分，只作参考，不计入总分'),
 'G': dict(w=None, text='总分≥3 五星；≥1 四星；≥-1 三星；≥-3 二星；否则一星'),
}
SPB = {'七杀', '破军', '贪狼'}
def majors(c, b): return {s['n'] for s in pal(c, b)['stars'] if s['t'] == 'major'} or set(pal(c, b)['borrowed'])
def find(c, name): return next(p for p in c['palaces'] if p['name'] == name)
def star_branch(c, n):
    for p in c['palaces']:
        if any(s['n'] == n for s in p['stars']): return p['branch']

def hepan(ka, kb, year=2026):
    A, B = CH[ka], CH[kb]; total = 0.0; why = []
    def add(v, rid, t):
        nonlocal total; total += v; why.append((rid, round(v, 2), t))
    for X, Y, nx, ny in ((A, B, 'A', 'B'), (B, A, 'B', 'A')):
        fx = majors(X, find(X, '夫妻')['branch']); my = majors(Y, Y['ming'])
        if fx & my: add(RULES['H1']['w'], 'H1', f'{nx}夫妻宫{"".join(fx)}对上{ny}命宫{"".join(my)}')
        for nm in ('夫妻', '福德'):
            p = find(X, nm); names = {s['n'] for s in p['stars']}
            if ('廉贞' in names and names & {'破军', '贪狼'}) or any(s['h'] == '忌' for s in p['stars']):
                add(RULES['H3']['w'], 'H3', f'{nx}{nm}宫({p["bz"]})见廉破/廉贪或化忌')
            sha = len(names & SIX_SHA)
            if sha: add(-0.5 * sha, 'H2', f'{nx}{nm}宫煞星{sha}颗')
            if any(s['h'] in ('禄', '权', '科') for s in p['stars']) or '禄存' in names: add(1.0, 'H2', f'{nx}{nm}宫见禄权科/禄存')
        g = X['input']['gender']; spouse_star = '太阴' if g == 'male' else '太阳'
        b = star_branch(X, spouse_star)
        if b is not None:
            st = next(s for s in pal(X, b)['stars'] if s['n'] == spouse_star)
            if st['h'] == '忌': add(RULES['H4']['w'], 'H4', f'{nx}{spouse_star}化忌')
            elif st['b'] == '陷': add(-0.5, 'H4', f'{nx}{spouse_star}落陷')
            elif st['b'] in ('庙', '旺'): add(0.5, 'H4', f'{nx}{spouse_star}庙旺')
        if any(s['n'] in ('红鸾',) for s in pal(X, X['ming'])['stars']): add(RULES['H9']['w'] * 0.5, 'H9', f'{nx}命带红鸾')
        # H8 生年四化落对方盘
        hz = {st['h']: st['n'] for p in X['palaces'] for st in p['stars'] if st['h']}
        lu, ji = hz.get('禄'), hz.get('忌')  # 生年四化直接取引擎本命盘
        bl, bj = star_branch(Y, lu), star_branch(Y, ji)
        if bl is not None and pal(Y, bl)['name'] in ('命宫', '财帛', '夫妻'): add(1.0, 'H8', f'{nx}生年禄({lu})落{ny}{pal(Y, bl)["name"]}')
        if bj is not None and pal(Y, bj)['name'] == '命宫': add(-1.5, 'H8', f'{nx}生年忌({ji})落{ny}命宫')
        if bj is not None and pal(Y, bj)['name'] == '夫妻': add(-2.0, 'H8', f'{nx}生年忌({ji})落{ny}夫妻宫')
    for X, Y, nx in ((A, B, 'A'),):
        if A['input']['gender'] == 'male' and majors(B, B['ming']) & {'七杀'}: add(RULES['H5']['w'], 'H5', 'B 七杀入命')
        if B['input']['gender'] == 'male' and majors(A, A['ming']) & {'七杀'}: add(RULES['H5']['w'], 'H5', 'A 七杀入命')
    if majors(A, A['ming']) & SPB and majors(B, B['ming']) & SPB: add(RULES['H6']['w'], 'H6', '双方命宫皆杀破狼')
    if (A['yearBranch'] - B['yearBranch']) % 12 == 6: add(RULES['H7']['w'], 'H7', '生肖对冲')
    da, db = reading(A, 'decade', year)['score']['love'], reading(B, 'decade', year)['score']['love']
    why.append(('H10', 0, f'{year}年两人所在大限的感情分：A {da} / B {db}（只作参考，不计入总分）'))
    stars = 5 if total >= 3 else 4 if total >= 1 else 3 if total >= -1 else 2 if total >= -3 else 1
    return dict(total=round(total, 2), stars=stars, reasons=why)

if __name__ == '__main__':
    r = hepan(sys.argv[1], sys.argv[2]); print(json.dumps(r, ensure_ascii=False, indent=1))
