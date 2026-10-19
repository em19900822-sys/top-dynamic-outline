# 顶部动态提纲

一个用于口播视频的 Codex Skill：从已经粗剪完成的真人口播视频中，生成可叠加在画面顶部的动态提纲层。

## 适用场景

- 主题标题固定在竖屏视频顶部
- 主播讲到新观点时，观点逐条出现并继续保留
- 进入新章节时清空旧观点并切换标题
- 需要透明提纲层、叠加预览和可回查的质量报告

## 不负责的内容

这个 Skill 不负责剪辑原视频、生成字幕、美颜、评分或完成最终成片。

## 输出

- `outline.json`：章节、主题、要点、出现时间和原文锚点
- `top-outline-alpha.mov`：透明背景、无音频的提纲层
- `top-outline-preview.mp4`：叠加到原视频上的观看预览
- `qc-report.json`：媒体参数、透明通道、时长、解码和布局检查

## 使用

将本仓库安装到 Codex Skill 目录后，重新打开 Codex，即可调用：

```text
$top-dynamic-outline
```

也可以直接表达任务：

```text
用 $top-dynamic-outline 给这条粗剪口播视频生成顶部动态提纲。
```

## 本地依赖

- Python
- FFmpeg 与 FFprobe
- 已经粗剪完成的口播视频
- 可选：已经校验过的 SRT、VTT、JSON 或逐字稿

Skill 默认只使用本地能力，不调用付费 API，也不覆盖输入视频。

## 目录

- `SKILL.md`：任务边界、内容规则、执行流程和验收标准
- `references/`：提纲字段、内容和布局规则
- `scripts/`：媒体探测、提纲验证、渲染和成品验证
- `tests/`：核心契约测试
- `agents/openai.yaml`：Codex 中的显示名和调用提示
