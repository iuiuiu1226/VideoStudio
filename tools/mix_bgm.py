#!/usr/bin/env python3
"""把背景音樂混進成片：音樂墊在人聲下方，有人講話時自動壓低（側鏈壓縮）。

  - 音樂基準音量 --music-db（相對音樂原始響度的增益，預設 -7 dB，講話時約比人聲低 20 dB）
    或 --rel：直接指定「音樂比人聲低幾 dB」（會先量兩者響度再自動算增益，例如 --rel -17）
  - 人聲出現時再壓低約 4–6 dB；沒人講話（例如片尾）時恢復
  - --music-eq：音樂先過等化，例如在人聲最需要的中頻讓出空間（音樂存在感不變、人聲更清楚）
  - --duck-ratio：講話時壓低音樂的力道（壓縮比）；--no-duck 則音樂維持固定音量（不會忽大忽小）
  - --start：音樂從第幾秒開始用；開頭短淡入、結尾 --fade-out 秒淡出
  - --lufs：整支響度調到目標（兩段式 loudnorm 線性調整，不改變人聲與音樂的比例）；沒給就只限幅
  - 最後加限幅器，避免爆音；影像串流直接複製

用法：
  python3 tools/mix_bgm.py output/完整版.mp4 output/bgm.wav -o output/完整版_配樂.mp4
  python3 tools/mix_bgm.py output/完整版.mp4 assets/music/x.mp3 --start 13 --rel -17 --no-duck --lufs -14 -o out.mp4
"""
import argparse
import json
import subprocess
import tempfile


def lufs(path, extra=()):
    r = subprocess.run(["ffmpeg", "-hide_banner", *extra, "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float([l.split()[1] for l in r.splitlines() if l.strip().startswith("I:")][-1])


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("music")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--music-db", type=float, default=-7.0)
    ap.add_argument("--rel", type=float, help="音樂比人聲低幾 dB（例如 -17），會覆蓋 --music-db")
    ap.add_argument("--music-eq", default="", help="音樂的等化（ffmpeg 濾鏡字串）")
    ap.add_argument("--duck-ratio", type=float, default=3.0)
    ap.add_argument("--no-duck", action="store_true", help="音樂固定音量，不隨人聲壓低")
    ap.add_argument("--start", type=float, default=0.0, help="音樂從第幾秒開始用")
    ap.add_argument("--fade-out", type=float, default=2.0)
    ap.add_argument("--lufs", type=float, help="整支響度目標（例如 -14）")
    args = ap.parse_args()

    dur = duration(args.video)
    music_db = args.music_db
    if args.rel is not None:
        voice = lufs(args.video)
        music = lufs(args.music, ["-ss", str(args.start), "-t", str(dur)])
        music_db = voice + args.rel - music
        print(f"人聲 {voice:.1f} LUFS、音樂 {music:.1f} LUFS → 音樂增益 {music_db:+.1f} dB（比人聲低 {-args.rel:.0f} dB）")

    graph = ("[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][key];"
             f"[1:a]atrim=start={args.start}:duration={dur},asetpts=PTS-STARTPTS,"
             f"aformat=sample_rates=48000:channel_layouts=stereo,"
             f"afade=t=in:d=0.3,afade=t=out:st={max(0.0, dur - args.fade_out):.3f}:d={args.fade_out},"
             f"{args.music_eq + ',' if args.music_eq else ''}volume={music_db:.2f}dB[m];"
             + ("[key]anullsink;[m]anull[duck];" if args.no_duck else
                f"[m][key]sidechaincompress=threshold=0.02:ratio={args.duck_ratio}:attack=40:release=800:knee=4[duck];") +
             "[v][duck]amix=inputs=2:duration=first:normalize=0")
    if args.lufs is None:
        graph += ",alimiter=limit=0.89:level=false[a]"
    else:
        # 先混好量響度，再線性調整到目標，比例不變
        with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video, "-i", args.music,
                            "-filter_complex", graph + "[a]", "-map", "[a]", tf.name], check=True)
            r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tf.name, "-af",
                                f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                               capture_output=True, text=True).stderr
        m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
        graph += (f",loudnorm=I={args.lufs}:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:"
                  f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                  f"offset={m['target_offset']},alimiter=limit=0.89:level=false,aresample=48000[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video, "-i", args.music,
                    "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", args.out], check=True)
    print(args.out)


if __name__ == "__main__":
    main()
