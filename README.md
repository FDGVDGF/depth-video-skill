# Depth Video Skill — 黑白深度视频 + 视频生成提示词

用 Depth Anything V2 Small，把一段视频转成黑白深度视频，再按人物图、场景图、深度视频写一份视频生成提示词，导出后拿去视频生成工具里用。

- 模型：Depth Anything V2 Small（ONNX fp16 导出，`onnx-community/depth-anything-v2-small`，与 PyTorch 原版同源）
- 本地运行：CPU 即可，不用 GPU，不用联网调云端模型
- 灰度规则：保留模型原本的灰度层次，不做 CLAHE、直方图均衡、gamma、逐帧对比度。只做一次全视频统一线性映射，越近越白、越远越黑
- 保留原视频比例、帧率、时长；有音频原样混回

## 快速开始

```bash
git clone https://github.com/FDGVDGF/depth-video-skill.git
cd depth-video-skill
bash install.sh
```

安装会做三件事：建 `venv/`、装 `requirements.txt`、下载 48MB 的 ONNX 模型到 `model_onnx/model_fp16.onnx`。模型不放在仓库里，GitHub 上下载后第一次安装时才下载。

需要先装好 Python 3.10+、ffmpeg、curl。

## 用法

### 1. 转黑白深度视频

```bash
bash scripts/run_depth.sh input.mp4 output/depth.mp4
```

先导出视频，再发提示词。输出是 H.264 MP4，宽高、帧率、时长和原视频一致，有音频就原样保留。

实测（4 核 CPU、无 GPU）：6 秒 720×1280、30fps 视频约 4.4 分钟，30 秒约 20 分钟。示例输出见 `examples/test-seg1-depth.mp4`。

为什么默认短边 256：全分辨率短边 518 在 CPU 上约 8 秒一帧，6 秒视频要约 48 分钟，不可用。短边 256 约 1.2 秒一帧，深度图本身是平滑的，推理完再双线性放大回原尺寸，人物轮廓保留完好。模型本身没换，改的是推理分辨率，这一点在 `scripts/convert_depth.py` 开头写明了。

### 2. 写提示词（只写，不生成）

按 `SKILL.md` 第 3 步和 `docs/PROMPT_FORMAT.md` 来，以后都按这个格式：

- 图片1：参考人物的脸、发型、服装和配饰
- 图片2：参考场景、光线和色调
- 视频1（黑白深度视频）：参考舞蹈动作、节奏和运镜
- 人物外观以图片1为准
- 先观察素材，再提炼主要动作和镜头变化，写得简洁连贯，不逐秒堆砌指令
- 无法读取素材时说明
- 时长、比例、人数按当次填写的为准

### 3. 导出提示词

```bash
./venv/bin/python scripts/export_prompt.py \
  --prompt-file prompt.txt \
  --title "粉色JK比耶" \
  --model "待填写" --duration "6秒" --ratio "9:16" --people "1人" \
  --person-ref "图片1：粉色JK人物图" \
  --scene-ref "图片2：米色墙面室内" \
  --depth-ref "视频1：test-seg1-depth.mp4 黑白深度视频" \
  --name "my-prompt"
```

导出两个文件到 `output/`：

- `my-prompt.md`：带模型、时长、比例、人数、三个参考的完整版
- `my-prompt.txt`：纯提示词正文，一字不改，可直接粘贴到视频生成工具

英文版只有提供了才导出，不凭空翻译。没填的字段写“待填写”，不编造。示例见 `examples/seg1-sample-prompt.md` 和 `examples/seg1-sample-prompt.txt`。

### 4. 生成视频

确认提示词后，再按提示词和已上传的素材生成视频。模型、时长、比例、人数按当次填写的为准，模型必须是已配置且支持这些参考的。人物以人物图为准，环境以场景图为准，动作和运镜参考视频。模型不支持某类参考，先说明，不要硬生成。

## 文件结构

```
depth-video-skill/
  README.md            本文件
  SKILL.md             给 Muse / AI 助手用的 skill 说明
  skill.yaml           skill 元数据
  install.sh           一键安装
  requirements.txt     onnxruntime + opencv + numpy
  scripts/
    convert_depth.py   转黑白深度视频
    export_prompt.py   导出提示词
    run_depth.sh       转视频的包装脚本
  examples/
    test-seg1-depth.mp4       示例深度视频（6秒，720x1280）
    seg1-sample-prompt.md     示例提示词完整版
    seg1-sample-prompt.txt    示例提示词纯文本
    sample-prompt.txt         示例提示词正文
  docs/
    WORKFLOW.md        四步完整流程
    PROMPT_FORMAT.md   提示词格式（v3，以后都按这个格式）
```

模型、虚拟环境、输出文件不在仓库里（见 `.gitignore`）。

## 许可证

代码用 Apache-2.0（见 `LICENSE`）。Depth Anything V2 Small 本身也是 Apache-2.0。模型权重按其原作者的许可使用，见 `onnx-community/depth-anything-v2-small` 和 `depth-anything/Depth-Anything-V2-Small-hf`。
