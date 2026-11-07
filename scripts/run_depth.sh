#!/bin/bash
# 用法：bash scripts/run_depth.sh 输入.mp4 输出.mp4
# 从仓库根目录运行，或从任意目录传绝对路径。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
./venv/bin/python scripts/convert_depth.py "$1" "$2"
