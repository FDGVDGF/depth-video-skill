#!/bin/bash
# 安装 Depth Video Skill：建 venv、装依赖、下载 ONNX 模型
# 用法：bash install.sh
# 要求：Python 3.10+、ffmpeg、curl、约 500MB 磁盘（venv 约 300MB + 模型 48MB）
set -e
cd "$(dirname "$0")"

echo "== 检查 =="
python3 --version
ffmpeg -version | head -1
curl --version | head -1

echo "== 建虚拟环境 =="
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "== 下载模型（Depth Anything V2 Small，ONNX fp16，48MB） =="
mkdir -p model_onnx
MODEL_URL="https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model_fp16.onnx"
if [ -f model_onnx/model_fp16.onnx ]; then
  echo "模型已存在，跳过下载：model_onnx/model_fp16.onnx"
else
  curl -L -C - -o model_onnx/model_fp16.onnx "$MODEL_URL"
fi
ls -lh model_onnx/model_fp16.onnx

echo "== 完成 =="
echo "转深度视频：bash scripts/run_depth.sh 输入.mp4 output/输出.mp4"
echo "导出提示词：./venv/bin/python scripts/export_prompt.py --prompt-file 提示词.txt --name my-prompt"
