from __future__ import annotations

import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


def probe_media(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe.exe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate:stream_tags=rotate",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    raw = json.loads(completed.stdout)
    streams = raw.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    rotate = int((video.get("tags") or {}).get("rotate") or 0)
    if abs(rotate) in (90, 270):
        display_width, display_height = height, width
    else:
        display_width, display_height = width, height
    rate_text = str(video.get("avg_frame_rate") or "0/1")
    fps = float(Fraction(rate_text)) if rate_text not in {"0/0", "0/1"} else 0.0
    duration = float((raw.get("format") or {}).get("duration") or 0)
    return {
        "source": str(path.resolve()),
        "duration_seconds": duration,
        "size_bytes": int((raw.get("format") or {}).get("size") or path.stat().st_size),
        "encoded_width": width,
        "encoded_height": height,
        "display_width": display_width,
        "display_height": display_height,
        "rotation": rotate,
        "fps": fps,
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "has_video": bool(video),
        "has_audio": bool(audio),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"找不到输入视频：{args.input}")
    report = probe_media(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "probe.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
