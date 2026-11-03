/** 运限用的单张盘导出。输入 stdin JSON: {"key":"x","y":2000,"m":1,"d":1,"gender":"male","lon":116.4,"hour":6}
 * hour 必须是已换算好的时辰序（xuan 先用 natal/hour_index.ts 做夏令时 + 真太阳时）。引擎目录由 XUAN_ENGINE 指定。 */
import { readFileSync } from 'fs';
const ENG = process.env.XUAN_ENGINE as string;
const { generateChart } = require(ENG + '/lib/ziwei/algorithm');
const { BRANCHES, STEMS } = require(ENG + '/lib/ziwei/constants');
const p = JSON.parse(readFileSync(0, 'utf8'));
const hour = p.hour;
const c = generateChart({ year: p.y, month: p.m, day: p.d, hour, gender: p.gender, city: '', longitude: p.lon } as any);
const out = {
  input: p, hour, hourBranch: BRANCHES[hour], tst: null,
  lunar: c.lunarInfo, yearStem: STEMS[c.lunarInfo.yearStem], yearBranch: c.lunarInfo.yearBranch,
  ming: c.mingGongBranch, shen: c.shenGongBranch, ju: c.wuxingJuName, yyg: c.yinYangGender,
  palaces: c.palaces.map((pl: any) => ({ branch: pl.branch, bz: BRANCHES[pl.branch], gz: STEMS[pl.stem] + BRANCHES[pl.branch], name: pl.name,
    isEmpty: !!pl.isEmpty, borrowed: pl.borrowedStars ?? [],
    stars: pl.stars.map((s: any) => ({ n: s.name, t: s.type, b: s.brightnessRaw ?? '', h: s.siHua ?? '' })) })),
  daxians: c.daXians.map((d: any) => ({ s: d.startAge, e: d.endAge, branch: d.palaceBranch, name: d.palaceName })),
};
console.log(JSON.stringify(out));
