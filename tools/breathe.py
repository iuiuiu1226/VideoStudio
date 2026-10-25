#!/usr/bin/env python3
"""幫每個片段留自然的氣口，避免「話還沒講完就切走」。

剪得太緊時，句尾的尾音和換氣會被切掉，聽起來像話沒講完。
這個工具分析素材音訊的響度，對每個片段：
  - 出點：等句尾聲音真正收掉，再保留最多 TAIL 秒的自然停頓，
          但一定停在下一個字開口之前（不會把下一句、訪問者的話剪進來）
  - 入點：如果前面是安靜的，往前多留最多 LEAD 秒，開口不會太突然
  - 片段可設 "tail" / "lead" 覆寫上限（訪問者緊接插話時設 0）
  - 字幕：跟著入點平移；句中停頓造成的字幕空檔（< 1.5 秒）補滿，最後一句延到片段結尾

只調整第一次執行時記下的原始切點（in0/out0），重複執行結果相同。

用法：
  python3 tools/breathe.py cuts/seg*.json --src <素材資料夾>
"""
import argparse
import json
import subprocess

import numpy as np

SR = 16000
HOP = 0.02          # 響度分析的時間解析度（秒）
TAIL = 0.35         # 句尾最多保留的停頓
LEAD = 0.12         # 開口前最多保留的安靜
GUARD = 0.06        # 與下一個字之間至少留的距離
MAX_TAIL_SKIP = 0.18  # 出點後若持續有聲超過這個長度，表示話沒停，出點維持不動

_cache = {}


def envelope(src):
    if src not in _cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR),
                              "-f", "s16le", "-"], capture_output=True, check=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        n = int(HOP * SR)
        frames = a[: len(a) // n * n].reshape(-1, n)
        _cache[src] = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    return _cache[src]


def adjust(env, t_in, t_out, tail=TAIL, lead=LEAD):
    i0, i1 = int(t_in / HOP), int(t_out / HOP)
    lo, hi = max(0, i0 - 100), min(len(env), i1 + 100)
    floor = np.percentile(env[lo:hi], 15)
    voiced = env > floor + 9

    # 出點：先走完句尾還在發聲的部分
    k = i1
    while k < len(env) and voiced[k] and (k - i1) * HOP < MAX_TAIL_SKIP:
        k += 1
    if k < len(env) and voiced[k]:
        new_out = t_out  # 話沒停（後面緊接著下一個字），不延長
    else:
        # 找下一個開口（連續 3 格有聲）
        j = k
        while j + 2 < len(env) and not (voiced[j] and voiced[j + 1] and voiced[j + 2]):
            j += 1
        new_out = min(k * HOP + tail, j * HOP - GUARD)
        new_out = max(new_out, t_out)

    # 入點：前面若是安靜的，往前留一點
    k = i0 - 1
    while k >= 0 and not voiced[k] and (i0 - k) * HOP <= lead:
        k -= 1
    new_in = max((k + 1) * HOP + GUARD / 2, t_in - lead)
    new_in = min(new_in, t_in)
    return round(new_in, 2), round(new_out, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlists", nargs="+")
    ap.add_argument("--src", required=True)
    args = ap.parse_args()

    for path in args.cutlists:
        sp = json.load(open(path, encoding="utf-8"))
        for c in sp["clips"]:
            if "card" in c:
                continue
            c.setdefault("in0", c["in"])
            c.setdefault("out0", c["out"])
            # 片段可用 "tail" / "lead" 覆寫（例如訪問者緊接著插話時設 0）
            new_in, new_out = adjust(envelope(f"{args.src}/{c['src']}"), c["in0"], c["out0"],
                                     c.get("tail", TAIL), c.get("lead", LEAD))
            shift = c["in0"] - new_in
            dur = new_out - new_in
            subs = [[round(s + shift, 2), round(e + shift, 2), t] for s, e, t in c.get("subs_orig", c["subs"])]
            c.setdefault("subs_orig", c["subs"])
            for a, b in zip(subs, subs[1:]):
                if 0 < b[0] - a[1] < 1.5:
                    a[1] = b[0]
            if subs:
                subs[0][0] = 0.0 if subs[0][0] <= shift + 0.01 else subs[0][0]
                subs[-1][1] = round(dur, 2)
            c["in"], c["out"], c["subs"] = new_in, new_out, subs
            print(f"{path} {c['id']}: 入 {c['in0']}→{new_in} (+{shift:.2f}s)  "
                  f"出 {c['out0']}→{new_out} (+{new_out - c['out0']:.2f}s)")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(sp, fh, ensure_ascii=False, indent=2)
            fh.write("\n")


if __name__ == "__main__":
    main()
