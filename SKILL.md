# 黑白深度视频 + 视频生成提示词

## 安装

- 先运行 `bash install.sh`，再做任何转换。
- 安装会建 `venv/`、装依赖、下载 ONNX 模型到 `model_onnx/model_fp16.onnx`。
- 模型不在仓库里，不要把 `venv/`、`model_onnx/`、`output/` 发到 GitHub。

## 转黑白深度视频

- 用 `bash scripts/run_depth.sh 输入.mp4 输出.mp4` 转换。
- 只用 Depth Anything V2 Small，推理短边默认 256。
- 保留模型原本的灰度层次，不做 CLAHE、直方图均衡、gamma、逐帧对比度。
- 只做一次全视频统一线性映射，全局 min/max 按整段视频统计，不按每帧算。
- 不反转深浅，越近越白、越远越黑。
- 保留原比例、帧率、帧数和时长，有音频用 ffmpeg 原样混回。
- 转换完抽帧检查人物有没有明显缺失，对比原视频同一时刻。
- 先导出视频，再发提示词。

## 写视频生成提示词

- 只在用户上传了人物图、场景图和黑白深度视频，并且说写提示词、暂时不要生成视频时才写。
- 图片1参考人物的脸、发型、服装和配饰，图片2参考场景、光线和色调，视频1参考舞蹈动作、节奏和运镜。
- 人物外观以图片1为准。
- 先观察素材，再提炼主要动作和镜头变化，写得简洁连贯，不逐秒堆砌指令。
- 无法读取素材时说明。
- 时长、比例、人数按用户当次填写的为准。

## 导出提示词

- 写完就用 `scripts/export_prompt.py` 导出，提示词正文一字不改。
- 导出两个文件到 `output/`：`<name>.md` 带模型、时长、比例、人数和三个参考的完整版，`<name>.txt` 是纯提示词正文，可直接粘贴到视频生成工具。
- 英文版只有提供了才导出，不凭空翻译。
- 没填的字段写“待填写”，不编造。
- 导出后把两个文件都交给用户检查，确认后才进下一步。

## 生成视频

- 只在用户在同一对话里确认了提示词，并且说按确认的提示词和已上传的素材生成视频时才生成。
- 模型、时长、比例、人数按用户当次填写的为准，模型必须是已配置且支持这些参考的。
- 人物以人物图为准，环境以场景图为准，动作和运镜参考视频。
- 模型不支持某类参考，先说明，不要硬生成。
- 完成后保存到用户指定的位置，并给文件路径。

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.
