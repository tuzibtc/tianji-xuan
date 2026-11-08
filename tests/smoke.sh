#!/usr/bin/env bash
# 冒烟测试（离线测试见 tests/env_and_backup.sh）：在一个干净的临时 XUAN_HOME 里跑一遍主要命令（用虚构人物）。需要网络（setup 会下载引擎和数据集）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; X="$ROOT/bin/xuan"
export XUAN_HOME="${XUAN_HOME:-$(mktemp -d)}"
echo "XUAN_HOME=$XUAN_HOME"
$X setup ${SETUP_ARGS:---years 1988-1988}
P="--date 1988-03-21 --gender female"
$X chart $P --clock 14:30 --lon 121.47 | grep -q '命宫'
$X natal $P --hour 7 --topics wealth | grep -q '仅供参考'
$X year  $P --hour 7 --year 2027 | grep -q '相对位置'
$X month $P --hour 7 --year 2026 --month 10 | grep -q '相对位置'
$X hepan --a-date 1988-03-21 --a-gender female --a-hour 7 --b-date 1988-11-02 --b-gender male --b-hour 2 | grep -q '星'
ID=$($X bugua cast --asker 测试 --q "测试问题" --coins 101100 --test | python3 -c "import json,sys;print(json.load(sys.stdin)['record']['id'])")
$X bugua show "$ID" | grep -q '雷火丰'
$X fengshui --rooms '{"西北":"厨房"}' --people '{"男主人":"东"}' | grep -q 'Y02'
$X xiang --part palm | grep -q 'P01'
$X cezi | grep -q '青龙'
LID=$($X log add --method cezi --asker 测试 --input 测试 --summary 测试 --test | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
$X log feedback "$LID" --verdict 准 --note 测试
$X calib-status | grep -q '校准状态'
echo "全部通过"
