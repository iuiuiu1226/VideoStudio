#!/usr/bin/env python3
"""把背景音樂混進成片：音樂墊在人聲下方，有人講話時自動壓低（側鏈壓縮）。

  - 音樂基準音量 --music-db（相對音樂原始響度的增益，預設 -7 dB，講話時約比人聲低 20 dB）
  - 人聲出現時再壓低約 4–6 dB；沒人講話（例如片尾）時恢復
  - 最後加限幅器，避免爆音；影像串流直接複製

用法：
  python3 tools/mix_bgm.py output/完整版.mp4 output/bgm.wav -o output/完整版_配樂.mp4
"""
import argparse
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("music")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--music-db", type=float, default=-7.0)
    args = ap.parse_args()

    graph = ("[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][key];"
             f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={args.music_db}dB[m];"
             "[m][key]sidechaincompress=threshold=0.02:ratio=3:attack=40:release=800:knee=4[duck];"
             "[v][duck]amix=inputs=2:duration=first:normalize=0,"
             "alimiter=limit=0.89:level=false[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video, "-i", args.music,
                    "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", args.out], check=True)
    print(args.out)


if __name__ == "__main__":
    main()
