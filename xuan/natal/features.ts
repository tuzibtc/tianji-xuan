// 用引擎为一张或多张盘导出特征（每行一个 key: YYYY-MM-DD-h-gender）。
// 引擎目录由环境变量 XUAN_ENGINE 指定（xuan setup 克隆的上游 ziwei-doushu，固定 commit）。
// 解读数据集 v4.0 按亮度流派 XD2 生成，所以默认 setBrightnessSchool('XD2')。
import * as readline from 'readline';
const ENG = process.env.XUAN_ENGINE as string;
const { generateChart, setBrightnessSchool } = require(ENG + '/lib/ziwei/algorithm');
setBrightnessSchool((process.env.BS as any) || 'XD2');
export function featuresOf(key: string) {
  const [y, m, d, h, g] = key.split('-');
  const c = generateChart({ year: +y, month: +m, day: +d, hour: +h, gender: g as any });
  const palaces = c.palaces.map((p: any) => ({
    n: p.name, b: p.branch, s: p.stem, shen: !!p.isShenGong, empty: !!p.isEmpty,
    st: p.stars.map((s: any) => [s.name, s.type, s.brightnessRaw ?? '', s.brightness ?? '', s.siHua ?? '']),
    self: (p.selfSihua ?? []).map((x: any) => x.starName + x.siHua),
  }));
  return { k: key, g, ju: c.wuxingJuName, mg: c.mingGongBranch, sg: c.shenGongBranch, mz: c.mingZhu, sz: c.shenZhu, ys: c.lunarInfo.yearStem, yb: c.lunarInfo.yearBranch,
    yyg: c.yinYangGender, dx: c.daXians.map((x: any) => [x.startAge, x.endAge, x.palaceBranch]), P: palaces };
}
const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (k) => { if (k.trim()) process.stdout.write(JSON.stringify(featuresOf(k.trim())) + '\n'); });
