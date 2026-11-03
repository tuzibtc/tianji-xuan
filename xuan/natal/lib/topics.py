TOPIC_PAL = {'overview':'命宫','personality':'命宫','love':'夫妻','career':'官禄','wealth':'财帛','health':'疾厄','family':'兄弟','children':'子女','move':'迁移','friends':'仆役','home':'田宅','spirit':'福德','parents':'父母'}
TOPICS = list(TOPIC_PAL)
def role_order(c, topic):
    n = TOPIC_PAL[topic]; p = c.pal(n); a, b = c.sanhe(n); o = c.opp(n)
    first = [n, a['n'], b['n'], o['n']]
    rest = [x['n'] for x in c.f['P'] if x['n'] not in first]
    keys = []
    for nm in first + rest:
        keys += ['D:' + nm, 'N:' + nm, 'A:' + nm]
    return keys + ['DXR1', 'DXR2']
