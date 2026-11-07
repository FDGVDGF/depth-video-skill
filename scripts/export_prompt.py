#!/usr/bin/env python3
"""
导出视频生成提示词
用法：
  ./venv/bin/python export_prompt.py \
    --prompt-file prompt.txt \
    --title "粉色JK比耶" \
    --model "待填写" --duration "6秒" --ratio "9:16" --people "1人" \
    --person-ref "图片1：粉色JK人物图" \
    --scene-ref "图片2：米色墙面室内" \
    --depth-ref "视频1：test-seg1-depth.mp4 黑白深度视频" \
    --name "seg1-sample"

输出（默认到 ./output/，可用 --output-dir 改）：
  <name>.md  — 带元数据的完整版，可直接打开复制
  <name>.txt — 纯提示词正文，一字不改，可直接粘贴到视频生成工具
规则：
- 提示词正文一字不改导出，不擅自加词、删词、改词。
- 英文版只有在调用方提供了才导出，不凭空翻译/编造。
- 元数据（模型/时长/比例/人数/参考素材）按当次填写的为准，空着就写“待填写”，不编造。
"""
import argparse
import os
from datetime import datetime

DEFAULT_OUT = os.path.join(os.getcwd(), "output")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True, help="提示词正文文件（中文）")
    ap.add_argument("--english-file", default=None, help="英文提示词文件（可选，有才导出）")
    ap.add_argument("--title", default="视频生成提示词")
    ap.add_argument("--model", default="待填写")
    ap.add_argument("--duration", default="待填写")
    ap.add_argument("--ratio", default="待填写")
    ap.add_argument("--people", default="待填写")
    ap.add_argument("--person-ref", default="待填写")
    ap.add_argument("--scene-ref", default="待填写")
    ap.add_argument("--depth-ref", default="待填写")
    ap.add_argument("--name", default=None)
    ap.add_argument("--output-dir", default=DEFAULT_OUT)
    args = ap.parse_args()

    with open(args.prompt_file, encoding="utf-8") as f:
        prompt = f.read().strip()
    english = None
    if args.english_file:
        with open(args.english_file, encoding="utf-8") as f:
            english = f.read().strip()

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    name = args.name or f"prompt-{stamp}"
    os.makedirs(args.output_dir, exist_ok=True)
    md_path = os.path.join(args.output_dir, f"{name}.md")
    txt_path = os.path.join(args.output_dir, f"{name}.txt")

    meta = (
        f"# {args.title}\n\n"
        f"- 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- 模型：{args.model}\n"
        f"- 时长：{args.duration}\n"
        f"- 比例：{args.ratio}\n"
        f"- 人数：{args.people}\n"
        f"- 人物参考：{args.person_ref}\n"
        f"- 场景参考：{args.scene_ref}\n"
        f"- 动作/运镜参考：{args.depth_ref}\n\n"
        f"## 提示词（中文，一字不改）\n\n{prompt}\n"
    )
    if english:
        meta += f"\n## 提示词（英文）\n\n{english}\n"
    meta += "\n---\n\n> 说明：提示词正文按确认版原样导出，未改动。模型不支持某类参考时，以第 4 步开始前的说明为准。\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(meta)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(prompt + "\n")

    print(f"已导出：\n{md_path}\n{txt_path}")


if __name__ == "__main__":
    main()
