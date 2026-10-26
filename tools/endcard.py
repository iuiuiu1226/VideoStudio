#!/usr/bin/env python3
"""產生片尾動畫（直式 1080x1920，無聲）。

畫面：深色底，Logo 淡入並輕微放大，接著文字由上而下依序淡入。
只用淡入與極小幅度的縮放，維持乾淨、專業的調性。

用法：
  python3 tools/endcard.py cuts/endcard.json --font <字型資料夾> -o output/endcard.mp4

設定檔欄位：
  logo, logo_h, logo_y：Logo 圖檔、高度、中心的垂直位置
  dur：總長（秒）
  bg：底色
  lines：[{"text", "y", "size", "color", "start"}]，color 為 RRGGBB，start 為淡入開始秒數
"""
import argparse
import json
import os
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
FADE = 0.6


def ass_color(rgb):
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H00{b}{g}{r}&".upper()


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--font", required=True)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    dur, font = cfg["dur"], cfg.get("font", "Noto Sans TC")
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "card.ass")
    with open(ass, "w", encoding="utf-8") as f:
        f.write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L,{font},60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,3,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        for ln in cfg["lines"]:
            fade_ms = int(FADE * 1000)
            bold = "" if ln.get("bold", True) else "\\b0"
            f.write(f"Dialogue: 0,{ass_time(ln['start'])},{ass_time(dur)},L,,0,0,0,,"
                    f"{{\\pos({W // 2},{ln['y']})\\fs{ln['size']}\\c{ass_color(ln.get('color', 'FFFFFF'))}"
                    f"{bold}\\fsp{ln.get('spacing', 3)}\\fad({fade_ms},0)}}{ln['text']}\n")

    lh, ly = cfg.get("logo_h", 280), cfg.get("logo_y", 700)
    # Logo：0.9 秒淡入，1.6 秒內由 94% 緩慢放大到 100%（ease-out）
    grow = f"(0.94+0.06*(1-pow(1-min(t/1.6\\,1)\\,3)))"
    graph = (f"[1:v]format=rgba,scale=w=-2:h='{lh}*{grow}':eval=frame,"
             f"fade=t=in:st=0.15:d=0.9:alpha=1[lg];"
             f"[0:v][lg]overlay=x=(W-w)/2:y={ly}-h/2:eval=frame:shortest=1,"
             f"subtitles={ass}:fontsdir={args.font},format=yuv420p[vo]")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"color=c={cfg.get('bg', '0x0E1118')}:s={W}x{H}:r={FPS}:d={dur}",
                    "-loop", "1", "-framerate", str(FPS), "-i", cfg["logo"],
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={dur}",
                    "-filter_complex", graph, "-map", "[vo]", "-map", "2:a",
                    "-t", str(dur), "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.out],
                   check=True)
    print(f"{args.out}  {dur}s")


if __name__ == "__main__":
    main()
