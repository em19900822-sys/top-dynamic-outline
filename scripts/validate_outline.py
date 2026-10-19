from __future__ import annotations

from typing import Any


MAX_ITEMS = 7
MAX_TEXT_LENGTH = 24


def validate_outline(probe: dict[str, Any], outline: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    duration = float(probe.get("duration_seconds") or 0)
    chapters = outline.get("chapters") if isinstance(outline, dict) else None
    if outline.get("schema_version") != 1:
        errors.append("schema_version 必须为 1")
    if not isinstance(chapters, list) or not chapters:
        errors.append("chapters 不能为空")
        return {"status": "fail", "errors": errors}
    previous_end = -1.0
    for chapter_index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            errors.append(f"第{chapter_index}个章节不是对象")
            continue
        title = str(chapter.get("title") or "").strip()
        start = float(chapter.get("start") or 0)
        end = float(chapter.get("end") or 0)
        items = chapter.get("items")
        if not title:
            errors.append(f"第{chapter_index}个章节缺少标题")
        if start < 0 or end <= start or end > duration + 0.05:
            errors.append(f"第{chapter_index}个章节时间范围无效")
        if start < previous_end - 0.05:
            errors.append(f"第{chapter_index}个章节与前一章节重叠")
        previous_end = end
        if not isinstance(items, list):
            errors.append(f"第{chapter_index}个章节 items 不是列表")
            continue
        if len(items) > MAX_ITEMS:
            errors.append(f"第{chapter_index}个章节最多7条要点")
        previous_item_start = start - 0.05
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"第{chapter_index}章第{item_index}条不是对象")
                continue
            text = str(item.get("text") or "").strip()
            item_start = float(item.get("start") or 0)
            source = str(item.get("source") or "").strip()
            if not text:
                errors.append(f"第{chapter_index}章第{item_index}条缺少文字")
            if len(text) > MAX_TEXT_LENGTH:
                errors.append(f"第{chapter_index}章第{item_index}条过长")
            if not source:
                errors.append(f"第{chapter_index}章第{item_index}条缺少原文锚点")
            if item_start < start - 0.05 or item_start > end + 0.05:
                errors.append(f"第{chapter_index}章第{item_index}条不在章节范围内")
            if item_start < previous_item_start - 0.05:
                errors.append(f"第{chapter_index}章要点时间不递增")
            previous_item_start = item_start
    return {"status": "pass" if not errors else "fail", "errors": errors}


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    parser.add_argument("outline", type=Path)
    args = parser.parse_args()
    report = validate_outline(
        json.loads(args.probe.read_text(encoding="utf-8")),
        json.loads(args.outline.read_text(encoding="utf-8")),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)
