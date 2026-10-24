#!/usr/bin/env python3
"""依剪輯清單（JSON）把素材剪成一段直式影片，並燒錄字幕。

用法：
  python3 tools/build_segment.py cuts/seg1_hook.json \
      --src <素材資料夾> --font <字型資料夾> -o output/seg1_hook.mp4

剪輯清單格式見 cuts/seg1_hook.json：
  每個 clip 指定 src、in、out（秒）、zoom（1.0 = 原始畫面），
  subs 是字幕列表，時間以「該 clip 的 in 點」為 0。
"""
import argparse
import json
import os
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
AFADE = 0.012  # 每個切點的音訊淡入淡出，避免爆音


def run(cmd):
    subprocess.run(cmd, check=True)


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(events, path, style):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font']},{style['size']},&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,2,0,1,{style['outline']},{style['shadow']},2,80,80,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for s, e, text in events:
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Default,,0,0,0,,{text}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist")
    ap.add_argument("--src", required=True)
    ap.add_argument("--font", required=True, help="含字型檔的資料夾")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    spec = json.load(open(args.cutlist, encoding="utf-8"))
    style = spec["style"]
    tmp = tempfile.mkdtemp()
    parts, events, t0 = [], [], 0.0

    for i, c in enumerate(spec["clips"]):
        dur = c["out"] - c["in"]
        z = c.get("zoom", 1.0)
        # 依 zoom 放大後裁回 1080x1920，裁切框偏上，保留臉部
        vf = (f"scale={int(W * z) // 2 * 2}:{int(H * z) // 2 * 2},"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{c.get('crop_y', 0.35)},"
              f"fps={FPS},format=yuv420p,setsar=1")
        af = f"afade=t=in:d={AFADE},afade=t=out:st={dur - AFADE:.3f}:d={AFADE}"
        part = os.path.join(tmp, f"p{i:02d}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c['in']}", "-t", f"{dur}",
             "-i", os.path.join(args.src, c["src"]), "-vf", vf, "-af", af,
             "-c:v", "libx264", "-preset", "medium", "-crf", "17",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", part])
        parts.append(part)
        for s, e, text in c.get("subs", []):
            events.append((t0 + s, t0 + min(e, dur), text))
        t0 += dur

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(tmp, "joined.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", joined])

    ass = os.path.join(tmp, "subs.ass")
    build_ass(events, ass, style)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", joined,
         "-vf", f"subtitles={ass}:fontsdir={args.font}",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", args.out])
    print(f"{args.out}  {t0:.2f}s")


if __name__ == "__main__":
    main()
