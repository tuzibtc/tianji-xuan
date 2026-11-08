# tianji-xuan

**English** · [中文](#中文)

A command-line toolkit for Zi Wei Dou Shu (紫微斗数) in the *Tianji* (《天纪》) tradition: chart casting, 13-topic natal readings, yearly / monthly / decade luck, compatibility (hepan), I Ching divination (卜卦), house feng shui (阳宅), face and palm reading (相法), character divination (测字), and feedback-based calibration. One entry point: `xuan`.

> Everything it outputs is a reference from a traditional-culture perspective, not a prediction, diagnosis, or investment or medical advice. Every conclusion ends with "仅供参考" (for reference only).

The data and command output are in Chinese. An assistant built on this tool should explain the results in whatever language the user speaks.

## Install

Requires git, Node.js ≥ 18 and Python ≥ 3.9.

```bash
git clone https://github.com/tuzibtc/tianji-xuan.git tianji-xuan && cd tianji-xuan
bin/xuan info             # first run creates the Python env in xuan-venv/ automatically
bin/xuan setup            # clones the pinned upstream engine, runs npm ci, downloads and verifies the dataset (~155 MB)
```

All data lives in `XUAN_HOME` (default `~/.local/share/tianji-xuan`): the engine, dataset, models, people file, logs and calibration state. The repository itself contains no data.

Optional: `bin/xuan train` trains the rebuilt reading model from the local dataset, for natal readings of people born before 1950 or after 2026 (a full run needs about 15 GB of RAM and several hours; see `xuan train -h` for a small trial run).

## Python environment and auto-rebuild

`bin/xuan` runs in a local env at `xuan-venv/` (override with `XUAN_VENV`). The name is deliberate: some hosting platforms skip directories named `.venv`, `venv`, `node_modules`, `build`, `dist`, `out`, `target` or `.cache` when they save and restore a workspace, so an env under those names can silently vanish.

Before every run `xuan` checks the env against the pinned versions in `requirements-lock.txt`. If it is missing or broken it rebuilds it with `scripts/rebuild_env.sh` and logs what it did to `$XUAN_HOME/env-rebuild.log`. Manual: `scripts/rebuild_env.sh [--check|--force]`. Set `XUAN_PYTHON` to use your own interpreter and skip the check. The upstream engine's `node_modules` lives under `XUAN_HOME`; if it disappears, run `bin/xuan setup` again.

## Backing up your own data

`scripts/backup_to_github.py` is a template for backing up your own data (by default `XUAN_HOME`) to **your own private** GitHub repo, using the `gh` CLI:

```bash
scripts/backup_to_github.py --repo <you>/<private-repo> --dry-run   # scan only, show what would be skipped
scripts/backup_to_github.py --repo <you>/<private-repo> --create    # create as private if missing, then push
```

It refuses if the repo is not private, never pushes to this code repo or the upstream engine repo, skips credential-like filenames and token/key-like contents, skips files over 50 MB (`--max-mb`) and environment/cache dirs, and writes `BACKUP_MANIFEST.json` listing every skipped item and why. It never deletes your source files. Add `--src PATH` (repeatable) for other folders.

## Usage

```bash
xuan chart  --date 1988-03-21 --gender female --clock 14:30 --lon 121.47   # chart (clock time → true solar time)
xuan natal  --date 1988-03-21 --gender female --hour 7 --topics wealth,career
xuan year   --date 1988-03-21 --gender female --hour 7 --year 2027
xuan month  --date 1988-03-21 --gender female --hour 7 --year 2026 --month 10   # lunar month
xuan hepan  --a-date 1988-03-21 --a-gender female --a-hour 7 --b-date 1986-11-02 --b-gender male --b-hour 2
xuan bugua  cast --asker user --q "Is this job change a good idea?" --coins 101100   # bottom line first, 1 = yang
xuan fengshui --rooms '{"西北":"厨房","东":"卧室"}' --people '{"男主人":"东"}'
xuan xiang  --part face      # face-reading rules
xuan cezi                    # character-divination rules
xuan log feedback <id> --verdict 准|不准|部分|未应 --note "what actually happened"   # accurate / inaccurate / partly / not yet
xuan calib-status
```

`--hour` is the double-hour index 0–11 (0 = 子 23:00–01:00, 1 = 丑, …). To use `--person <id>`, copy the format of `people.example.json` into `XUAN_HOME/people.json`.

## Public mode

`XUAN_PUBLIC=1` is the default: no internal confidence labels, no source attributions, episode numbers or timecodes, and "仅供参考" at the end of each conclusion. Set `XUAN_PUBLIC=0` during development to see the internal labels.

## Calibration

Each method (divination, feng shui, physiognomy, character divination, luck periods) keeps its own log. Accurate = 1, partly = 0.5, inaccurate = 0; "not yet" and test runs don't count. A method is reviewed after every 30 new feedback entries, and it passes once it has at least 100 entries since its last rule change with ≥ 90% accuracy.

## License and sources

- Code: MIT (see `LICENSE`, which keeps the upstream engine's copyright notice).
- The chart engine and the reading dataset come from upstream [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu). They are downloaded at install time, not distributed here; the dataset is CC BY 4.0, with attribution in `NOTICE`.
- This repository contains no text, lecture notes or transcripts from *Tianji*; rules and method notes are written in our own words.

---

<a id="中文"></a>

## 中文

基于《天纪》体系的紫微斗数命令行工具：排盘、本命 13 维解读、流年 / 流月 / 大限、合盘、卜卦、阳宅、相法、测字，以及按反馈校准。一个入口：`xuan`。

> 所有输出都只是传统文化角度的参考，不构成任何预测、诊断、投资或医疗建议。每个结论末尾都会附上「仅供参考」。

### 安装

需要：git、Node.js ≥ 18、Python ≥ 3.9。

```bash
git clone https://github.com/tuzibtc/tianji-xuan.git tianji-xuan && cd tianji-xuan
bin/xuan info             # 第一次运行会自动在 xuan-venv/ 建好 Python 环境
bin/xuan setup            # 克隆固定版本的上游引擎 + npm ci + 下载并校验解读数据集（约 155 MB）
```

数据都放在 `XUAN_HOME`（默认 `~/.local/share/tianji-xuan`）：引擎、数据集、模型、人物库、日志、校准状态。仓库本身不含任何数据。

可选：`bin/xuan train` 用本机数据集训练自建论断库，给 1950 年前或 2027 年后出生的人做本命解读（全量需要约 15 GB 内存、数小时；可先用小参数试跑，见 `xuan train -h`）。

### Python 环境与自动重建

`bin/xuan` 使用本地环境 `xuan-venv/`（可用 `XUAN_VENV` 改位置）。特意不用 `.venv`、`venv`、`node_modules`、`build`、`dist`、`out`、`target`、`.cache` 这些名字：有些托管平台保存和恢复工作区时会按名字跳过它们，环境会悄悄消失。

每次运行前 `xuan` 会按 `requirements-lock.txt` 里锁定的版本自检；缺失或损坏就用 `scripts/rebuild_env.sh` 自动重建，并把过程记到 `$XUAN_HOME/env-rebuild.log`。手动：`scripts/rebuild_env.sh [--check|--force]`。设了 `XUAN_PYTHON` 则直接用你指定的解释器、不自检。上游引擎的 `node_modules` 在 `XUAN_HOME` 里，丢了重跑一次 `bin/xuan setup` 即可。

### 备份自己的数据

`scripts/backup_to_github.py` 是一个备份模板，用 `gh` 把你自己的数据（默认 `XUAN_HOME`）备份到**你自己的私有** GitHub 库：

```bash
scripts/backup_to_github.py --repo <你>/<私有库> --dry-run   # 只扫描，列出会跳过什么
scripts/backup_to_github.py --repo <你>/<私有库> --create    # 不存在就建成私有库，然后推送
```

目标库不是私有就拒绝；绝不推到本代码库或上游引擎库；跳过像凭据的文件名和像令牌/密钥的内容；跳过超过 50 MB 的文件（`--max-mb`）和环境/缓存目录，并写出 `BACKUP_MANIFEST.json` 说明每个跳过项及原因。不会删除任何源文件。其他目录用 `--src 路径`（可重复）。

### 用法

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

### 公开模式

默认 `XUAN_PUBLIC=1`：不显示内部置信标签，过滤人名出处、集数、时间码和「出处」类段落，每个结论末尾加「仅供参考」。开发时可设 `XUAN_PUBLIC=0` 查看内部标签。

### 校准

每种方法（卜卦、阳宅、相法、测字、运限）各自记日志。准=1、部分=0.5、不准=0，未应和试跑不计。上次复盘后新增满 30 条有效反馈就复盘一次；上次改规则后满 100 条且准确率 ≥ 90%，这个方法就算过关。

### 许可与来源

- 代码：MIT（见 `LICENSE`，保留上游引擎版权声明）。
- 排盘引擎与解读数据集来自上游 [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu)，安装时下载，不随本仓库分发；数据集为 CC BY 4.0，来源标注见 `NOTICE`。
- 本仓库不包含《天纪》原文、讲义或文字稿；规则与方法说明均为自己的话整理。

改项目名：`scripts/rename.sh 新名字`。
