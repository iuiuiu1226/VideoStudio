#!/usr/bin/env python3
"""逐段檢查成片的響度與峰值，確認每個人、每一段的音量接近一致。

用法：
  python3 tools/check_loudness.py output/完整版.mp4 cuts/seg1_hook.json cuts/seg2_how.json ...
"""
import json
import re
import subprocess
import sys

FPS = 30


def main():
    video, cutlists = sys.argv[1], sys.argv[2:]
    t, vals = 0.0, []
    for path in cutlists:
        for c in json.load(open(path, encoding="utf-8"))["clips"]:
            dur = round(((c["dur"]) if "card" in c else c["out"] - c["in"]) * FPS) / FPS
            if "card" not in c and not c.get("no_overlay"):
                r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t:.3f}", "-t", f"{dur:.3f}", "-i", video,
                                    "-af", "ebur128=peak=true", "-f", "null", "-"],
                                   capture_output=True, text=True).stderr
                lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
                peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
                vals.append(lufs)
                print(f"{c['src']:16s} {c['id']:18s} {t:6.1f}s  {lufs:6.1f} LUFS  峰值 {peak:5.1f} dBFS")
            t += dur
    print(f"響度範圍 {min(vals):.1f} ~ {max(vals):.1f} LUFS（差 {max(vals) - min(vals):.1f} dB，建議 2 dB 以內）")


if __name__ == "__main__":
    main()
