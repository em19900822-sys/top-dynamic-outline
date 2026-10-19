from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-v{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"输出文件冲突太多：{path}")


def escaped_number(value: float) -> str:
    return f"{value:.3f}"


def build_filter(outline: dict[str, Any], width: int, height: int) -> str:
    title_size = max(28, int(width * 0.042))
    item_size = max(24, int(width * 0.033))
    title_y = int(height * 0.032)
    line_y = int(height * 0.078)
    first_item_y = int(height * 0.097)
    row_gap = int(height * 0.036)
    filters: list[str] = []
    for chapter in outline["chapters"]:
        start = float(chapter["start"])
        end = float(chapter["end"])
        title = str(chapter["title"])
        title_file = f"title-{chapter['id']}.txt"
        filters.append(
            "drawtext="
            f"fontfile='msyhbd.ttc':textfile='{title_file}':fontcolor=white:"
            f"fontsize={title_size}:borderw=1:bordercolor=black@0.85:shadowx=3:shadowy=3:"
            f"shadowcolor=black@0.9:x=(w-text_w)/2:y={title_y}:"
            f"enable='between(t,{escaped_number(start)},{escaped_number(end)})':"
            f"alpha='if(lt(t,{escaped_number(start)}),0,if(lt(t,{escaped_number(start + 0.5)}),"
            f"(t-{escaped_number(start)})/0.5,1))'"
        )
        filters.append(
            f"drawbox=x={int(width * 0.19)}:y={line_y}:w={int(width * 0.62)}:h={max(2, int(height * 0.0015))}:"
            f"color=white@0.9:t=fill:enable='between(t,{escaped_number(start)},{escaped_number(end)})'"
        )
        for index, item in enumerate(chapter.get("items") or []):
            item_start = float(item["start"])
            item_file = f"item-{chapter['id']}-{index + 1}.txt"
            y = first_item_y + row_gap * index
            filters.append(
                "drawtext="
                f"fontfile='msyhbd.ttc':textfile='{item_file}':fontcolor=white:"
                f"fontsize={item_size}:borderw=1:bordercolor=black@0.9:shadowx=3:shadowy=3:"
                f"shadowcolor=black@0.92:x='if(lt(t,{escaped_number(item_start)}),{int(width * 0.095)},"
                f"if(lt(t,{escaped_number(item_start + 0.4)}),{int(width * 0.095)}+{int(width * 0.025)}*"
                f"(t-{escaped_number(item_start)})/0.4,{int(width * 0.12)}))':y={y}:"
                f"enable='between(t,{escaped_number(item_start)},{escaped_number(end)})':"
                f"alpha='if(lt(t,{escaped_number(item_start)}),0,if(lt(t,{escaped_number(item_start + 0.4)}),"
                f"(t-{escaped_number(item_start)})/0.4,1))'"
            )
    if not filters:
        raise ValueError("outline 没有可渲染章节")
    return ",".join(filters)


def render(input_path: Path, outline_path: Path, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    from media_probe import probe_media

    probe = probe_media(input_path)
    (out_dir / "probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    width = int(probe["display_width"])
    height = int(probe["display_height"])
    duration = float(probe["duration_seconds"])
    fps = float(probe["fps"] or 30.0)
    font_source = Path(r"C:\Windows\Fonts\msyhbd.ttc")
    if not font_source.exists():
        raise RuntimeError("找不到中文字体 C:\\Windows\\Fonts\\msyhbd.ttc")
    alpha_path = unique_path(out_dir / "top-outline-alpha.mov")
    preview_path = unique_path(out_dir / "top-outline-preview.mp4")
    with tempfile.TemporaryDirectory(prefix="top-outline-") as temp_name:
        temp = Path(temp_name)
        shutil.copy2(font_source, temp / "msyhbd.ttc")
        for chapter in outline["chapters"]:
            (temp / f"title-{chapter['id']}.txt").write_text(str(chapter["title"]), encoding="utf-8")
            for index, item in enumerate(chapter.get("items") or [], start=1):
                (temp / f"item-{chapter['id']}-{index}.txt").write_text(str(item["text"]), encoding="utf-8")
        filter_text = build_filter(outline, width, height)
        transparent_input = f"color=c=black@0.0:s={width}x{height}:r={fps}:d={duration},format=rgba"
        alpha_result = run(
            [
                "ffmpeg.exe", "-y", "-f", "lavfi", "-i", transparent_input,
                "-vf", filter_text, "-t", f"{duration:.3f}", "-an",
                "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                str(alpha_path), "-loglevel", "warning",
            ],
            cwd=temp,
        )
        if alpha_result.returncode != 0:
            raise RuntimeError(f"透明层渲染失败：{alpha_result.stderr[-1200:]}")
        preview_result = run(
            [
                "ffmpeg.exe", "-y", "-i", str(input_path), "-i", str(alpha_path),
                "-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto[v]",
                "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(preview_path), "-loglevel", "warning",
            ]
        )
        if preview_result.returncode != 0:
            raise RuntimeError(f"预览合成失败：{preview_result.stderr[-1200:]}")
    return {"alpha": str(alpha_path.resolve()), "preview": str(preview_path.resolve())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("outline", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.input, args.outline, args.out_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
