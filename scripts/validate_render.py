from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe.exe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def duration(data: dict[str, Any]) -> float:
    return float((data.get("format") or {}).get("duration") or 0)


def resolution_matches(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left.get("width") == right.get("width") and left.get("height") == right.get("height")


def validate(input_path: Path, out_dir: Path) -> dict[str, Any]:
    alpha = out_dir / "top-outline-alpha.mov"
    preview = out_dir / "top-outline-preview.mp4"
    errors: list[str] = []
    if not alpha.exists():
        errors.append("缺少透明层")
    if not preview.exists():
        errors.append("缺少预览")
    if errors:
        return {"status": "fail", "errors": errors}
    source_data = probe(input_path)
    alpha_data = probe(alpha)
    preview_data = probe(preview)
    source_duration = duration(source_data)
    alpha_duration = duration(alpha_data)
    preview_duration = duration(preview_data)
    alpha_stream = next((s for s in alpha_data.get("streams", []) if s.get("codec_type") == "video"), {})
    preview_stream = next((s for s in preview_data.get("streams", []) if s.get("codec_type") == "video"), {})
    source_stream = next((s for s in source_data.get("streams", []) if s.get("codec_type") == "video"), {})
    if abs(source_duration - alpha_duration) > 1 / 30 + 0.05:
        errors.append("透明层时长与输入视频不一致")
    if abs(source_duration - preview_duration) > 1 / 30 + 0.05:
        errors.append("预览时长与输入视频不一致")
    if alpha_stream.get("pix_fmt") not in {"yuva444p10le", "yuva444p12le", "argb", "rgba"}:
        errors.append(f"透明层没有可确认的 alpha 像素格式：{alpha_stream.get('pix_fmt')}")
    for label, stream in (("透明层", alpha_stream), ("预览", preview_stream)):
        if not resolution_matches(stream, source_stream):
            errors.append(f"{label}分辨率与输入视频不一致")
    for label, path in (("透明层", alpha), ("预览", preview)):
        decoded = subprocess.run(["ffmpeg.exe", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0", "-f", "null", "-"], capture_output=True, text=True)
        if decoded.returncode != 0:
            errors.append(f"{label}完整解码失败")
    report = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "source_duration_seconds": source_duration,
        "alpha_duration_seconds": alpha_duration,
        "preview_duration_seconds": preview_duration,
        "alpha_pixel_format": alpha_stream.get("pix_fmt"),
        "alpha_stream": alpha_stream,
        "preview_stream": preview_stream,
        "input_stream": source_stream,
    }
    (out_dir / "qc-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()
    report = validate(args.input, args.out_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
