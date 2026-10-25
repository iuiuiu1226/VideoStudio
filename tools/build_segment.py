#!/usr/bin/env python3
"""依剪輯清單（JSON）把素材剪成一段直式影片，並燒錄字幕。

用法：
  python3 tools/build_segment.py cuts/seg1_hook.json [cuts/seg2_how.json ...] \
      --src <素材資料夾> --font <字型資料夾> -o output/seg1_hook.mp4

剪輯清單格式見 cuts/seg1_hook.json：
  每個 clip 指定 src、in、out（秒）、zoom（1.0 = 原始畫面），
  subs 是字幕列表，時間以「該 clip 的 in 點」為 0。
  問題字卡：{"card": "文字", "dur": 秒數}，深色底置中白字、無聲。
"""
import argparse
import json
import os
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
AFADE = 0.012  # 每個切點的音訊淡入淡出，避免爆音
TARGET_LUFS = -16.0


def run(cmd):
    subprocess.run(cmd, check=True)


def measure_lufs(src, start, dur):
    """量測素材某段的整合響度（LUFS），用來逐段對齊音量。"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{start}", "-t", f"{dur}", "-i", src,
                        "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    vals = [l.split()[1] for l in r.stderr.splitlines() if l.strip().startswith("I:")]
    try:
        return float(vals[-1])
    except (IndexError, ValueError):
        return None


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
Style: Card,{style['font']},{style.get('card_size', 84)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,0,0,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for s, e, text, st in events:
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},{st},,0,0,0,,{text}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlists", nargs="+", help="可給多個，依序接成一支")
    ap.add_argument("--src", required=True)
    ap.add_argument("--font", required=True, help="含字型檔的資料夾")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    specs = [json.load(open(p, encoding="utf-8")) for p in args.cutlists]
    style = specs[0]["style"]
    spec = {"clips": [c for sp in specs for c in sp["clips"]]}
    tmp = tempfile.mkdtemp()
    # 全部在同一條濾鏡鏈裡剪接：每段長度先對齊到整數影格，音訊裁成同樣長度，
    # 避免分段輸出再串接時的影格補齊與 AAC 前置延遲累積，造成字幕與音畫漂移
    inputs, chains, labels, events, t0 = [], [], [], [], 0.0
    n_in = 0

    for i, c in enumerate(spec["clips"]):
        raw = c["dur"] if "card" in c else c["out"] - c["in"]
        dur = round(raw * FPS) / FPS
        if "card" in c:
            inputs += ["-f", "lavfi", "-i",
                       f"color=c={style.get('card_bg', '0x141414')}:s={W}x{H}:r={FPS}:d={dur}",
                       "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={dur}"]
            vi, ai = n_in, n_in + 1
            n_in += 2
            vf = f"format=yuv420p,setsar=1"
            af = "anull"
            events.append((t0, t0 + dur, c["card"], "Card"))
        else:
            inputs += ["-ss", f"{c['in']}", "-t", f"{dur + 0.2}",
                       "-i", os.path.join(args.src, c["src"])]
            vi = ai = n_in
            n_in += 1
            if "frame" in c:
                # tools/autoframe.py 算好的裁切框：同一人各段大小、位置一致
                fr = c["frame"]
                vf = (f"crop={fr['w']:.1f}:{fr['h']:.1f}:{fr['x']:.1f}:{fr['y']:.1f},"
                      f"scale={W}:{H}:flags=lanczos,format=yuv420p,setsar=1")
            else:
                z = c.get("zoom", 1.0)
                # 依 zoom 放大後裁回 1080x1920，裁切框偏上，保留臉部
                vf = (f"scale={int(W * z) // 2 * 2}:{int(H * z) // 2 * 2},"
                      f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{c.get('crop_y', 0.35)},"
                      f"format=yuv420p,setsar=1")
            # 逐段把響度拉到同一基準，不同手機、不同距離錄的人聲才不會忽大忽小
            src = os.path.join(args.src, c["src"])
            lufs = measure_lufs(src, c["in"], dur)
            gain = 0.0 if lufs is None or lufs < -60 else max(-12.0, min(12.0, TARGET_LUFS - lufs))
            # 人聲做成雙單聲道（左右相同），手機喇叭、單聲道裝置都能正常出聲
            af = ("pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,"
                  f"highpass=f=80,volume={gain:.2f}dB,"
                  f"afade=t=in:d={AFADE},afade=t=out:st={dur - AFADE:.4f}:d={AFADE}")
            for s, e, text in c.get("subs", []):
                events.append((t0 + s, t0 + min(e, dur), text, "Default"))
        chains.append(f"[{vi}:v]fps={FPS},trim=duration={dur:.4f},setpts=PTS-STARTPTS,{vf}[v{i}]")
        chains.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,"
                      f"apad,atrim=duration={dur:.4f},asetpts=PTS-STARTPTS,{af}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
        t0 += dur

    ass = os.path.join(tmp, "subs.ass")
    build_ass(events, ass, style)
    graph = ";".join(chains) + ";" + "".join(labels) + \
        f"concat=n={len(labels)}:v=1:a=1[vc][ac];" \
        f"[vc]subtitles={ass}:fontsdir={args.font}[vo];" \
        "[ac]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[ao]"
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph,
         "-map", "[vo]", "-map", "[ao]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", args.out])
    print(f"{args.out}  {t0:.2f}s")


if __name__ == "__main__":
    main()
