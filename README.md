# tianji-xuan

基于《天纪》体系的紫微斗数命令行工具：排盘、本命 13 维解读、流年 / 流月 / 大限、合盘、卜卦、阳宅、相法、测字，以及按反馈校准。一个入口：`xuan`。

> 所有输出都只是传统文化角度的参考，不构成任何预测、诊断、投资或医疗建议。每个结论末尾都会附上「仅供参考」。

## 安装

需要：git、Node.js ≥ 18、Python ≥ 3.9。

```bash
git clone https://github.com/tuzibtc/tianji-xuan.git tianji-xuan && cd tianji-xuan
python3 -m pip install -r requirements.txt
bin/xuan setup            # 克隆固定版本的上游引擎 + npm ci + 下载并校验解读数据集（约 155 MB）
bin/xuan info             # 查看安装状态
```

数据都放在 `XUAN_HOME`（默认 `~/.local/share/tianji-xuan`）：引擎、数据集、模型、人物库、日志、校准状态。仓库本身不含任何数据。

可选：`bin/xuan train` 用本机数据集训练自建论断库，给 1950 年前或 2027 年后出生的人做本命解读（全量需要约 15 GB 内存、数小时；可先用小参数试跑，见 `xuan train -h`）。

## 用法

```bash
xuan chart  --date 1988-03-21 --gender female --clock 14:30 --lon 121.47   # 排盘（钟表时间 → 真太阳时）
xuan natal  --date 1988-03-21 --gender female --hour 7 --topics wealth,career
xuan year   --date 1988-03-21 --gender female --hour 7 --year 2027          # 流年：只报一生里的相对位置
xuan month  --date 1988-03-21 --gender female --hour 7 --year 2026 --month 10
xuan hepan  --a-date 1988-03-21 --a-gender female --a-hour 7 --b-date 1986-11-02 --b-gender male --b-hour 2
xuan bugua  cast --asker 用户 --q "这次换工作合适吗" --coins 101100            # 由下往上，1=阳
xuan fengshui --rooms '{"西北":"厨房","东":"卧室"}' --people '{"男主人":"东"}'
xuan xiang  --part face      # 相法规则表
xuan cezi                    # 测字规则表
xuan log feedback <id> --verdict 准|不准|部分|未应 --note "实际情况"
xuan calib-status
```

人物库：把 `people.example.json` 的格式抄到 `XUAN_HOME/people.json`，之后可以用 `--person <id>`。

## 公开模式

默认 `XUAN_PUBLIC=1`：不显示内部置信标签，过滤人名出处、集数、时间码和「出处」类段落，每个结论末尾加「仅供参考」。开发时可设 `XUAN_PUBLIC=0` 查看内部标签。

## 校准

每种方法（卜卦、阳宅、相法、测字、运限）各自记日志。准=1、部分=0.5、不准=0，未应和试跑不计。上次复盘后新增满 30 条有效反馈就复盘一次；上次改规则后满 100 条且准确率 ≥ 90%，这个方法就算过关。

## 许可与来源

- 代码：MIT（见 `LICENSE`，保留上游引擎版权声明）。
- 排盘引擎与解读数据集来自上游 [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu)，安装时下载，不随本仓库分发；数据集为 CC BY 4.0，来源标注见 `NOTICE`。
- 本仓库不包含《天纪》原文、讲义或文字稿；规则与方法说明均为自己的话整理。

改项目名：`scripts/rename.sh 新名字`。
