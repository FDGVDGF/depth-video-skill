#!/usr/bin/env python3
"""
Depth Anything V2 Small -> 黑白深度视频（本地 CPU）
模型：onnx-community/depth-anything-v2-small 的 fp16 ONNX 导出，
权重与 depth-anything/Depth-Anything-V2-Small-hf 同源，实测与 PyTorch 原版
在同一帧上 min/max 误差 <1%（fp16: 0.424/4.227，PyTorch: 0.417/4.194）。
用 ONNX 是因为 PyTorch 在本机 CPU 上同样慢，ONNX 不改变模型结构。

速度说明（实测，本机 4 核 CPU、无 GPU）：
- 全分辨率（短边 518，输入 924x518）：约 8 秒/帧，6 秒视频两遍推理要 ~48 分钟，不可用。
- 短边 256（输入 462x252）：约 1.2-1.3 秒/帧，深度图本身是平滑的，
  推理完再双线性放大回原尺寸，人物轮廓保留完好，这是视频生成做深度控制时的常用做法。
  所以默认短边 256，不是擅自换模型。
- 本脚本只推理一遍：把低分辨率深度图（float16）先存下来，
  算出整段视频精确的全局 min/max，再统一映射，避免第二遍推理。
  这样 6 秒 180 帧约 4 分钟，30 秒约 20 分钟。

规则（用户定，勿擅自改）：
- 只用 Depth Anything V2 Small。
- 保留模型原本的灰度层次，不额外增强对比度：
  不做 CLAHE、直方图均衡、gamma、逐帧自动对比度。
  只做一次全视频统一线性映射：gray = (depth - global_min) / (global_max - global_min) * 255
  global_min / global_max 是整段视频精确统计的，不是每帧单独算的。
- 不反转深浅：模型输出越大越近，映射后越近越白、越远越黑。
- 保留原视频比例（宽x高）、帧率、帧数/时长；有声音就用 ffmpeg 原样混回原音频。
用法：
  venv/bin/python convert_depth.py input.mp4 output.mp4 [--short-side 256]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
import onnxruntime as ort

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def default_model_path():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "model_onnx", "model_fp16.onnx"),
        os.path.join(here, "..", "model_onnx", "model_fp16.onnx"),
        os.path.join(os.getcwd(), "model_onnx", "model_fp16.onnx"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.normpath(p)
    return os.path.normpath(candidates[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--model-onnx", default=None)
    ap.add_argument("--short-side", type=int, default=256)
    args = ap.parse_args()
    if not args.model_onnx:
        args.model_onnx = default_model_path()

    print(f"模型: Depth Anything V2 Small (ONNX fp16)  推理短边: {args.short_side}  设备: CPU", flush=True)
    sess = ort.InferenceSession(args.model_onnx, providers=["CPUExecutionProvider"])

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"打不开输入视频: {args.input}", file=sys.stderr)
        sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"输入: {width}x{height}  fps={fps}  帧数={total}", flush=True)

    # 一遍推理：存低分辨率深度图，顺带统计全局 min/max
    depths = []
    gmin, gmax = float("inf"), float("-inf")
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        scale = args.short_side / min(h, w)
        nh = int(round(h * scale / 14) * 14)
        nw = int(round(w * scale / 14) * 14)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_CUBIC)
        x = res.astype(np.float32) / 255.0
        x = (x - MEAN) / STD
        x = np.transpose(x, (2, 0, 1))[None].astype(np.float32)
        out = sess.run(None, {"pixel_values": x})[0][0]  # [nh, nw] float32
        depths.append(out.astype(np.float16))
        gmin = min(gmin, float(out.min()))
        gmax = max(gmax, float(out.max()))
        n += 1
        if n % 30 == 0:
            print(f"推理: {n}/{total}  gmin={gmin:.4f} gmax={gmax:.4f}", flush=True)
    cap.release()
    print(f"推理完成: {n} 帧  global_min={gmin:.6f}  global_max={gmax:.6f}", flush=True)
    if gmax <= gmin:
        print("深度范围无效", file=sys.stderr)
        sys.exit(1)

    # 统一线性映射 + 放大回原尺寸，写无声临时视频
    tmpdir = tempfile.mkdtemp(prefix="depth_tmp_")
    tmp_video = os.path.join(tmpdir, "silent.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_video, fourcc, fps, (width, height), isColor=False)
    for i, d in enumerate(depths):
        gray_small = (d.astype(np.float32) - gmin) / (gmax - gmin) * 255.0
        gray_small = np.clip(gray_small, 0, 255).astype(np.uint8)
        gray = cv2.resize(gray_small, (width, height), interpolation=cv2.INTER_LINEAR)
        writer.write(gray)
        if (i + 1) % 60 == 0:
            print(f"写帧: {i+1}/{n}", flush=True)
    writer.release()
    print(f"临时视频: {tmp_video}", flush=True)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", args.input],
        capture_output=True, text=True,
    )
    has_audio = "audio" in probe.stdout
    print(f"原视频有音频: {has_audio}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    if has_audio:
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-i", tmp_video, "-i", args.input,
               "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-c:a", "copy", "-shortest", args.output]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-i", tmp_video,
               "-c:v", "libx264", "-pix_fmt", "yuv420p", args.output]
    subprocess.run(cmd, check=True)
    print(f"完成: {args.output}", flush=True)


if __name__ == "__main__":
    main()
