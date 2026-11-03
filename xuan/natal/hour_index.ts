// 钟表时间 → 排盘日 + 时辰序号（引擎的夏令时 / 钟表校正 / 真太阳时）。
// 用法: tsx hour_index.ts Y M D HH MM [经度]；引擎目录由 XUAN_ENGINE 指定。
const ENG = process.env.XUAN_ENGINE as string;
const { isChinaDST } = require(ENG + '/lib/ziwei/dst-cn');
const { calculateTrueSolarTime, resolveZiweiDayOffset, shiftGregorianDate, formatTrueSolarClock } = require(ENG + '/lib/ziwei/true-solar-time');
const [Y, M, D, H, MI, LON] = process.argv.slice(2).map(Number);
const dst = isChinaDST(Y, M, D);
let date = { year: Y, month: M, day: D };
let h = H, mi = MI;
if (dst) { // 夏令时钟表比北京标准时快 1 小时
  const raw = H * 60 + MI - 60; const off = Math.floor(raw / 1440);
  date = shiftGregorianDate(date, off); const r = ((raw % 1440) + 1440) % 1440; h = Math.floor(r / 60); mi = r % 60;
}
const r = calculateTrueSolarTime({ ...date, clockHour: h, clockMinute: mi, longitude: Number.isFinite(LON) ? LON : undefined });
const off = resolveZiweiDayOffset(r, 'next-day');
const chartDate = shiftGregorianDate(date, off);
console.log(JSON.stringify({ input: `${Y}-${M}-${D} ${H}:${MI}`, chinaDST: dst, beijingStandard: `${h}:${String(mi).padStart(2, '0')}`,
  trueSolar: formatTrueSolarClock(r), totalCorrectionMin: +r.totalCorrectionMinutes.toFixed(2), chartDate, hourIndex: r.branch }));
