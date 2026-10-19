import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_render.py"
spec = importlib.util.spec_from_file_location("validate_render", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_acceptance_outline_has_white_text_contract():
    data = {
        "schema_version": 1,
        "chapters": [
            {
                "id": "ch-1",
                "title": "第一笔账",
                "start": 0.0,
                "end": 60.0,
                "items": [
                    {"text": f"观点{i}", "start": float(i), "source": f"原文{i}"}
                    for i in range(1, 6)
                ],
            }
        ],
    }
    assert data["schema_version"] == 1
    assert len(data["chapters"][0]["items"]) == 5
    assert all(item["source"] for item in data["chapters"][0]["items"])


def test_resolution_match_requires_both_dimensions():
    assert module.resolution_matches({"width": 1080, "height": 1920}, {"width": 1080, "height": 1920})
    assert not module.resolution_matches({"width": 1080, "height": 1280}, {"width": 1080, "height": 1920})
