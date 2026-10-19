# outline.json 契约

```json
{
  "schema_version": 1,
  "chapters": [
    {
      "id": "ch-1",
      "title": "第一笔账",
      "start": 2.0,
      "end": 58.0,
      "items": [
        {
          "text": "普通人的峰值停留更久",
          "start": 8.0,
          "source": "普通人排卵时激素峰值往往会在高位停留一整天"
        }
      ]
    }
  ]
}
```

`start`、`end` 和每条要点的 `start` 都是相对于输入视频开头的秒数。章节按时间顺序排列，不重叠。`source` 是用于回查时间点的原文片段，不是展示文本。

非法示例：

```json
{"schema_version": 1, "chapters": [{"title": "", "start": 20, "end": 10, "items": []}]}
```
