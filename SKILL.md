---
name: top-dynamic-outline
description: Generate a standalone top dynamic outline video layer from a rough-cut talking-head video. Use when the user wants a topic title above the speaker and short points to appear one by one during speech, remain accumulated, and reset at a new topic. This skill only creates the outline layer, its preview, timeline JSON, and QC report; it does not cut, subtitle, beautify, score, or finish the source video.
metadata:
  short-description: Generate top dynamic outline overlay video
---

# 顶部动态提纲

这个 Skill 只做一个任务：根据已经粗剪完成的口播视频，生成可以叠加到原视频上的顶部动态提纲视频层。

## 输入

- 粗剪完成的视频路径。
- 可选：已经校验过的 SRT、VTT、JSON 或逐字稿。
- 可选：用户指定的主题、条数、字号、位置和输出目录。

没有可靠的真实时间戳时，先使用可用的本地转录能力从最终粗剪视频获取时间轴。禁止按总字数、段落长度或平均分配时间。

## 输出

在独立输出目录生成：

- `outline.json`：章节、主题、要点、出现时间和原文锚点。
- `top-outline-alpha.mov`：透明背景、无音频、可叠加的动态提纲层。
- `top-outline-preview.mp4`：将提纲叠加到原视频上的观看预览，保留原音频。
- `qc-report.json`：媒体参数、alpha、时间、解码和布局检查结果。

不覆盖输入视频。已有输出文件自动使用新版本名或停止并报告冲突。

## 内容规则

1. 先读完整口播，再划分章节和观点。
2. 每章有一个简短主题标题。
3. 主播讲到一个观点时，该观点才出现；已经出现的观点继续保留。
4. 进入新章节时清空旧列表并换标题。
5. 每条观点尽量一行，默认每章最多 5 条，安全区允许时最多 7 条。
6. 要点必须能在原文中找到对应锚点；健康内容不补充主播没有说过的医疗结论或效果承诺。

提纲字段和内容审查规则见 [references/outline-schema.md](references/outline-schema.md) 与 [references/content-rules.md](references/content-rules.md)。

## 默认视觉规则

- 竖屏顶部安全区；主题居中，观点左对齐。
- 文字固定白色。
- 使用黑色阴影或细描边保证在亮背景上可读。
- 不使用大块不透明底板。
- 新条目使用约 0.4 秒淡入和短距离移动；旧条目不重复动画。
- 不遮挡人物脸部、头部、底部字幕或免责声明。

布局细节见 [references/layout-rules.md](references/layout-rules.md)。

## 执行流程

1. 读取视频和已有时间轴，生成 `probe.json`。
2. 由 Codex 根据转录语义建立 `outline.json`，并回查每条原文锚点。
3. 运行 `scripts/validate_outline.py` 验证时间、章节、条数和文字长度。
4. 运行 `scripts/render_outline.py` 生成透明层和叠加预览。
5. 运行 `scripts/validate_render.py`，完整检查 alpha、时长、方向、画面和音视频解码。
6. 只有 `qc-report.json` 为 `pass` 才交付。

## 工具边界

- 使用本地 Python、FFmpeg 和 ffprobe；不默认调用付费 API。
- 本 Skill 不修改、不导入、不依赖 OpenMontage 的项目文件、checkpoint 或渲染脚本。
- 如需新的付费服务、云端模型或模型下载，先说明用途、费用上限和停止条件并取得用户授权。

## 入口命令

```powershell
python scripts/media_probe.py <input.mp4> --out-dir <output>
python scripts/validate_outline.py <probe.json> <outline.json>
python scripts/render_outline.py <input.mp4> <outline.json> --out-dir <output>
python scripts/validate_render.py <input.mp4> <output>
```
