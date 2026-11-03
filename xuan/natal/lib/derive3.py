"""派生串 · 第三批（健康：倪师疾厄真法“全盘杀星最集中之宫”、生年化忌坐宫→脏腑）。
规则由 v4 公开数据逆推：杀星=擎羊陀罗火星铃星地空地劫天空 + 生年化忌星；
按宫计数取最大；并列 ≤3 宫取自寅宫起顺数第一个；最大值为 1（全散）或并列 ≥4 宫 → “杀星分散”。
返回 (derived dict, extra tokens)。"""
BR = '子丑寅卯辰巳午未申酉戌亥'
SHA7 = ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫', '天空']
ORGAN = {'子': '胆', '丑': '肝', '寅': '肺', '卯': '大肠', '辰': '胃', '巳': '脾（中医运化之脾）', '午': '心（先天心气）',
         '未': '小肠', '申': '膀胱', '酉': '肾（中医之肾）', '戌': '心包（后天心气）', '亥': '三焦（水液代谢通道）'}
def derived3(c):
    d = {}; T = set(); cnt = {}; hj = None
    for p in c.f['P']:
        v = []
        for s in p['st']:
            if s[4] == '忌': v.append(s[0] + '化忌'); hj = (s[0], BR[p['b']], p['n'])
            elif s[0] in SHA7: v.append(s[0])
        if v: cnt[p['b']] = v
    if hj:
        d['HJX'] = f'（{hj[0]}）坐{hj[1]}宫→对应脏腑【{ORGAN[hj[1]]}】'
    if cnt:
        mx = max(len(v) for v in cnt.values())
        top = sorted([b for b in cnt if len(cnt[b]) == mx], key=lambda b: (b - 2) % 12)
        T.add('WP:mx=%d' % min(mx, 4)); T.add('WP:ntie=%d' % min(len(top), 4))
        if mx == 1 or len(top) >= 4:
            T.add('WP:split'); bs = sorted(cnt, key=lambda b: (b - 2) % 12) if mx == 1 else top
            d['WSPL'] = '、'.join(BR[b] for b in bs) + f'宫各 {mx} 处'
            d['WSPLB'] = '、'.join(f'**{BR[b]}宫**' for b in bs) + f' 这几宫，每宫 {mx} 处'
        else:
            T.add('WP:conc'); b = top[0]
            for i, bb in enumerate(top[:3]):
                br = BR[bb]; v = cnt[bb]; sa = '、'.join(v[:3]) + ('等' if len(v) > 3 else '')
                if i < 2: d['WPX%d' % (i + 1)] = f'{br}宫（{sa}）→对应脏腑【{ORGAN[br]}】'
                d['WPXB%d' % (i + 1)] = f'**{br}宫**（{'、'.join(v)}）→ 对应脏腑 **{ORGAN[br]}**'
            br = BR[b]
            T.add('WP:pal=' + c.byb[b]['n'])
            if hj and hj[1] == br: T.add('WP:hasji')
            T.add('WP:jipal_eq' if hj and hj[1] == br else 'WP:jipal_ne')
    T |= rel_tokens(c)
    from derive2 import derived2
    from derive import derived
    dx = c.cur_dx()
    if dx >= 0:   # 应期行：当前大限(起-止岁)走【X宫】：主星[原始亮度]…／空宫（官方原文命宫写作“命宫宫”，照录）
        s0, e0, b0 = c.f['dx'][dx]; p0 = c.byb[b0]; mj = c.majors(p0)
        d['YQ'] = f"当前大限({s0}-{e0}岁)走【{p0['n']}宫】：" + ('、'.join(f'{x[0]}[{x[2]}]' for x in mj) if mj else '空宫')
    d2 = derived2(c)
    for k in list(d2) + list(d):
        T.add('has:' + k)
    for k, v in d2.items(): d.setdefault(k, v)   # pre2 早于 TMK 加入 → 以此为准
    return d, T

RK = ['禄存', '化禄', '化权', '化科', '化忌', '天马', '擎羊', '陀罗', '火星', '铃星', '地空', '地劫', '天空', '旬空', '截空',
      '左辅', '右弼', '文昌', '文曲', '天魁', '天钺', '紫微', '天府']
def rel_tokens(c):
    """关系 token：两星同宫 co: / 互在三方四正 sf: / 对宫 op:（让学习器能表达“禄马同宫”之类格局条件）"""
    import collections
    T = set(); pos = collections.defaultdict(set)
    for p in c.f['P']:
        for s in p['st']:
            if s[0] in RK: pos[s[0]].add(p['b'])
            if s[4]: pos['化' + s[4]].add(p['b'])
    for i, a in enumerate(RK):
        for b in RK[i + 1:]:
            A, B = pos[a], pos[b]
            if not A or not B: continue
            if A & B: T.add(f'co:{a}+{b}')
            if any(((x - y) % 12) in (0, 4, 8, 6) for x in A for y in B): T.add(f'sf:{a}+{b}')
            if any(((x - y) % 12) == 6 for x in A for y in B): T.add(f'op:{a}+{b}')
    return T
