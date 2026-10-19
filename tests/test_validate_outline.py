import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_outline.py"
spec = importlib.util.spec_from_file_location("validate_outline", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def probe():
    return {
        "duration_seconds": 60.0,
        "display_width": 1080,
        "display_height": 1920,
        "fps": 30.0,
    }


def test_valid_outline_passes():
    outline = {
        "schema_version": 1,
        "chapters": [
            {
                "id": "ch-1",
                "title": "第一笔账",
                "start": 2.0,
                "end": 58.0,
                "items": [
                    {"text": "普通人的峰值停留更久", "start": 8.0, "source": "普通人排卵"},
                    {"text": "多囊峰值可能像闪电", "start": 18.0, "source": "峰值是闪电型"},
                ],
            }
        ],
    }
    report = module.validate_outline(probe(), outline)
    assert report["status"] == "pass"


def test_rejects_overlapping_chapters_and_late_item():
    outline = {
        "schema_version": 1,
        "chapters": [
            {
                "id": "ch-1",
                "title": "一",
                "start": 0,
                "end": 30,
                "items": [{"text": "观点", "start": 31, "source": "原文"}],
            },
            {"id": "ch-2", "title": "二", "start": 29, "end": 50, "items": []},
        ],
    }
    report = module.validate_outline(probe(), outline)
    assert report["status"] == "fail"
    assert any("章节重叠" in error or "不在章节范围" in error for error in report["errors"])


def test_rejects_more_than_seven_items_and_long_text():
    items = [{"text": "这是一个超过手机竖屏顶部安全区承载能力的长句" * 3, "start": i, "source": "原文"} for i in range(1, 9)]
    outline = {
        "schema_version": 1,
        "chapters": [{"id": "ch-1", "title": "标题", "start": 0, "end": 59, "items": items}],
    }
    report = module.validate_outline(probe(), outline)
    assert report["status"] == "fail"
    assert any("最多7条" in error for error in report["errors"])
    assert any("过长" in error for error in report["errors"])
