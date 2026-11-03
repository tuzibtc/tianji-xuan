#!/usr/bin/env bash
# 项目改名：scripts/rename.sh 新名字   （同时改 xuan/project.py 的 PROJECT 和文档里的旧名字）
set -e
NEW="$1"; [ -n "$NEW" ] || { echo "用法: $0 新名字"; exit 1; }
cd "$(dirname "$0")/.."
OLD=$(python3 -c "import sys; sys.path.insert(0,'xuan'); from project import PROJECT; print(PROJECT)")
grep -rl --exclude-dir=.git -- "$OLD" . | xargs sed -i "s/$OLD/$NEW/g"
echo "已把 $OLD 改成 $NEW（注意：默认数据目录 ~/.local/share/$NEW 也随之改变）"
