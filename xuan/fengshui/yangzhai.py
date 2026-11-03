#!/usr/bin/env python3
"""阳宅检查（确定性部分）：输入各方位房间用途 + 谁住哪，输出命中规则和每个人的「名位卦」。
例：xuan fengshui --rooms '{"中":"客厅","西北":"厨房","东":"卧室","北":"厕所"}' --people '{"男主人":"东","女主人":"东"}'
身份：男主人 / 女主人 / 长子 / 长女 / 次子 / 次女 / 幼子 / 幼女"""
import argparse, json, os
D = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(D, 'rules.json')))
H = json.load(open(os.path.join(os.path.dirname(D), 'bugua', 'hexagrams.json')))['hexagrams']
SEC = R['sectors']
FAM = {'男主人': '乾', '丈夫': '乾', '父': '乾', '女主人': '坤', '妻': '坤', '母': '坤', '长子': '震', '长女': '巽', '次子': '坎', '中男': '坎', '次女': '离', '中女': '离', '幼子': '艮', '少男': '艮', '幼女': '兑', '少女': '兑'}
TRI = {'乾': '111', '兑': '110', '离': '101', '震': '100', '巽': '011', '坎': '010', '艮': '001', '坤': '000'}
def hexa(upper, lower): return next(h for h in H if h['bits'] == TRI[lower] + TRI[upper])
p = argparse.ArgumentParser(prog='xuan fengshui'); p.add_argument('--rooms', required=True); p.add_argument('--people', default='{}'); a = p.parse_args()
rooms = json.loads(a.rooms); people = json.loads(a.people)
hit = []
def add(i, extra=''):
    r = next(x for x in R['rules'] if x['id'] == i); hit.append(dict(id=i, 结论=r['then'] + extra, 白话=r['user_wording']))
use = lambda s: rooms.get(s, '')
if '厕' in use('中'): add('Y01')
if '厨' in use('西北'): add('Y02')
if '厨' in use('西南'): add('Y03')
if '厨' in use('东'): add('Y04')
if '厨' in use('北'): add('Y05')
if any(k in use('西北') for k in ('客厅', '走道', '无', '缺')) or not use('西北'): add('Y06')
if '厕' in use('西北'): add('Y07')
if '厕' in use('东'): add('Y08')
if any(k in use('东') for k in ('客厅', '餐厅', '无', '缺')) or not use('东'): add('Y09')
if people.get('男主人') == '西南' or people.get('丈夫') == '西南': add('Y11')
if people.get('男主人') == '西北' and people.get('女主人') == '西北': add('Y12')
for who, sec in people.items():
    if sec == '北' and who in ('男主人', '女主人', '丈夫', '妻', '父', '母'): add('Y13', f'（{who}）')
gua = []
for who, sec in people.items():
    if who in FAM and sec in SEC:
        h = hexa(FAM[who], SEC[sec])
        gua.append(dict(人=who, 住=sec, 卦=f"{h['full_name']}（上{FAM[who]}＝身份，下{SEC[sec]}＝方位）", 卦辞=h['guaci'], 大象=h['daxiang'],
                        摘要=h['summary'], 名位相符=('是' if FAM[who] == SEC[sec] else '否')))
print(json.dumps(dict(命中规则=hit, 名位卦=gua, 提醒=R['rules'][-1]['user_wording'],
                      需人工判断=['户型中心点与方位是否量准', '缺角 / 不规则户型', '命盘合参（命里是否有这方面的问题）', '调整方案是否可行']), ensure_ascii=False, indent=1))
