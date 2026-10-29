#!/usr/bin/env python3
"""依剪輯清單（JSON）把素材剪成一段直式影片，並燒錄字幕。

用法：
  python3 tools/build_segment.py cuts/seg1_hook.json [cuts/seg2_how.json ...] \
      --src <素材資料夾> --font <字型資料夾> -o output/seg1_hook.mp4

剪輯清單格式見 cuts/seg1_hook.json：
  每個 clip 指定 src、in、out（秒）、zoom（1.0 = 原始畫面），
  subs 是字幕列表，時間以「該 clip 的 in 點」為 0。
  frame 是固定裁切框；frame_keys 是逐格裁切框（t 為素材秒數，之間線性內插）；
  v_in 讓畫面取自另一個時間點（聲音仍從 in 開始）。
  fx 是特效字（亮黃粗體、置中對齊，位置與動畫用 ASS 標籤寫在文字裡），時間是素材秒數。
  gain_keys 是段落內的音量曲線（t 為素材秒數、db 為增益）；style.loudness = "linear" 時整支只做固定增益＋限幅。
  問題字卡：{"card": "文字", "dur": 秒數}，深色底置中白字、無聲。
  overlay 是疊在畫面上的透明動畫檔（例如 qtrle 含 alpha 的 .mov），從該 clip 開頭對齊，疊在字幕底下。
  xfade 是跟前一段的交叉淡化秒數（畫面溶接）；前一段結尾要留至少這麼長的空白聲音（會被剪掉），
  這一段的聲音從自己的開頭照常播放，不會被淡掉。
"""
import argparse
import json
import os
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
AFADE = 0.012  # 每個切點的音訊淡入淡出，避免爆音
TARGET_LUFS = -16.0
MAX_GAIN = 24.0


def run(cmd):
    subprocess.run(cmd, check=True)


# iPhone 預設拍 HDR（HLG／PQ、BT.2020）。直接當一般影片處理會偏亮、偏淡，要先轉成一般畫面（SDR、BT.709）。
# mobius 色調映射＋HDR_NPL 的亮度基準，最接近手機上看原片的樣子
HDR_NPL = 600
HDR_TRC = ("arib-std-b67", "smpte2084")


def tonemap_chain(trc="arib-std-b67", npl=HDR_NPL):
    # zoompan 輸出的畫面不帶色彩標記，先用 setparams 補回 HDR 的標記，zscale 才知道要從哪裡轉
    return (f"setparams=color_primaries=bt2020:color_trc={trc}:colorspace=bt2020nc:range=tv,"
            f"zscale=t=linear:npl={npl},format=gbrpf32le,"
            "zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,")


def is_hdr(src):
    """HDR 素材回傳它的轉換曲線名稱（給 tonemap_chain），一般素材回傳空字串。"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=color_transfer", "-of", "default=nw=1:nk=1", src], capture_output=True, text=True)
    trc = r.stdout.strip().splitlines()[0].strip(",") if r.stdout.strip() else ""
    return trc if trc in HDR_TRC else ""


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


def lerp_expr(keys, k, var="it"):
    """把關鍵框的某個欄位寫成 ffmpeg 運算式（var = 片段內的秒數），關鍵框之間線性內插。"""
    expr = f"{keys[-1][k]:.2f}"
    for a, b in reversed(list(zip(keys, keys[1:]))):
        expr = (f"if(lt({var},{b['t']:.3f}),"
                f"{a[k]:.2f}+({b[k] - a[k]:.2f})*({var}-{a['t']:.3f})/{b['t'] - a['t']:.3f},{expr})")
    return f"if(lt({var},{keys[0]['t']:.3f}),{keys[0][k]:.2f},{expr})"


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
Style: Title,{style['font']},{style.get('title_size', 60)},&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,3,0,1,{style['outline']},{style['shadow']},{style.get('title_align', 8)},{style.get('title_margin_l', 80)},80,{style.get('title_margin', 200)},1
Style: Note,{style['font']},{style.get('note_size', 32)},&H50FFFFFF,&H50FFFFFF,&H80202020,&H00000000,0,0,0,0,100,100,2,0,1,2,0,{style.get('title_align', 8)},{style.get('title_margin_l', 80)},80,{style.get('note_margin', 275)},1
Style: Card,{style['font']},{style.get('card_size', 84)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,0,0,5,80,80,0,1
Style: Fx,{style['font']},{style.get('fx_size', 96)},&H004DD8FF,&H004DD8FF,&H00202020,&H80000000,-1,0,0,0,100,100,2,0,1,6,2,5,0,0,0,1

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
    starts, xfades, durs = [], [], []  # 每段在成片的開始時間、與前一段的交叉淡化秒數、長度
    spans = []  # 人物畫面的時間區段（字卡不放標題、Logo）
    n_in = 0

    for i, c in enumerate(spec["clips"]):
        raw = c["dur"] if "card" in c else c["out"] - c["in"]
        dur = round(raw * FPS) / FPS
        xf = round(c.get("xfade", 0.0) * FPS) / FPS if i > 0 else 0.0
        t0 -= xf  # 交叉淡化：這段提早 xf 秒開始，跟前一段重疊
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
            # src 可以是素材資料夾裡的檔名，或已存在的路徑（例如 output/endcard.mp4）
            src = c["src"] if os.path.exists(c["src"]) else os.path.join(args.src, c["src"])
            inputs += ["-ss", f"{c['in']}", "-t", f"{dur + 0.2}", "-i", src]
            vi = ai = n_in
            n_in += 1
            if "v_in" in c:
                # 畫面取自另一個時間點（例如聲音先進來，畫面還停在全場舉手的鏡頭）
                inputs += ["-ss", f"{c['v_in']}", "-t", f"{dur + 0.2}", "-i", src]
                vi = n_in
                n_in += 1
            if "frame_keys" in c:
                # 逐格裁切框（拍攝時鏡頭推拉，用來把人物大小補償回來）：
                # [{"t", "x", "y", "h"}, ...]，t 是素材時間（秒），之間線性內插；寬度固定為 h 的 9/16
                v0 = c.get("v_in", c["in"])
                keys = [{**k, "t": k["t"] - v0} for k in c["frame_keys"]]
                vf = (f"zoompan=z='ih/({lerp_expr(keys, 'h')})'"
                      f":x='{lerp_expr(keys, 'x')}':y='{lerp_expr(keys, 'y')}'"
                      f":d=1:s={W}x{H}:fps={FPS},format=yuv420p,setsar=1")
            elif "frame" in c:
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
            trc = is_hdr(src)
            if trc:
                vf = vf.replace("format=yuv420p,setsar=1", tonemap_chain(trc) + "format=yuv420p,setsar=1")
            # 逐段把響度拉到同一基準，不同手機、不同距離錄的人聲才不會忽大忽小
            # "auto_gain": false 時不自動對齊，只用 gain_db／gain_keys（音量曲線已經算好絕對大小時用）
            lufs = measure_lufs(src, c["in"], dur) if c.get("auto_gain", True) else None
            # 降噪後的素材可能很小聲，上限放寬到 ±MAX_GAIN；"gain_db" 可逐段微調
            gain = 0.0 if lufs is None or lufs < -70 else max(-MAX_GAIN, min(MAX_GAIN, TARGET_LUFS - lufs))
            gain += c.get("gain_db", 0.0)
            # 人聲做成雙單聲道（左右相同），手機喇叭、單聲道裝置都能正常出聲；浮點運算避免補音量時破音
            # gain_keys：段落內的音量曲線 [{"t", "db"}, ...]（t 是素材秒數），補償講者離手機忽遠忽近
            ride = ""
            if "gain_keys" in c:
                gk = [{**k, "t": k["t"] - c["in"]} for k in c["gain_keys"]]
                ride = f"volume='pow(10,({lerp_expr(gk, 'db', 't')})/20)':eval=frame,"
            af = ("aformat=sample_fmts=fltp,pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,"
                  f"highpass=f=80,volume={gain:.2f}dB,{ride}"
                  f"afade=t=in:d={AFADE},afade=t=out:st={dur - AFADE:.4f}:d={AFADE}")
            for s, e, text in c.get("subs", []):
                events.append((t0 + s, t0 + min(e, dur), text, "Default"))
            # 特效字（搞笑字卡、圖示）：[開始, 結束, 文字]，時間是素材秒數；文字可含 ASS 標籤（位置、動畫）
            for s, e, text in c.get("fx", []):
                a, b = max(0.0, s - c["in"]), min(dur, e - c["in"])
                if b > a:
                    events.append((t0 + a, t0 + b, text, "Fx"))
            if c.get("no_overlay"):
                pass  # 片尾等畫面不放標題、Logo
            elif spans and t0 <= spans[-1][1] + 1e-6:
                spans[-1][1] = t0 + dur  # 相接或交叉淡化重疊的段落合併，標題不會重複疊兩行
            else:
                spans.append([t0, t0 + dur])
        if c.get("overlay"):
            # 透明動畫疊加層（穿插的圖卡、標籤），對齊這段開頭
            inputs += ["-i", c["overlay"]]
            oi = n_in
            n_in += 1
            chains.append(f"[{vi}:v]fps={FPS},trim=duration={dur:.4f},setpts=PTS-STARTPTS,{vf}[b{i}]")
            chains.append(f"[{oi}:v]fps={FPS},trim=duration={dur:.4f},setpts=PTS-STARTPTS,format=rgba[o{i}]")
            chains.append(f"[b{i}][o{i}]overlay=0:0:eof_action=pass,format=yuv420p[v{i}]")
        else:
            chains.append(f"[{vi}:v]fps={FPS},trim=duration={dur:.4f},setpts=PTS-STARTPTS,{vf}[v{i}]")
        chains.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,"
                      f"apad,atrim=duration={dur:.4f},asetpts=PTS-STARTPTS,{af}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
        starts.append(t0)
        xfades.append(xf)
        durs.append(dur)
        t0 += dur

    def audio_join(out_label):
        # 下一段要交叉淡化時，這段結尾的空白聲音剪掉同樣長度，讓下一段的聲音照常從頭播放
        parts, trims = [], []
        for i in range(len(labels)):
            cut = xfades[i + 1] if i + 1 < len(labels) else 0.0
            if cut > 0:
                trims.append(f"[a{i}]atrim=duration={durs[i] - cut:.4f},asetpts=PTS-STARTPTS[at{i}]")
                parts.append(f"[at{i}]")
            else:
                parts.append(f"[a{i}]")
        return ";".join(trims + ["".join(parts) + f"concat=n={len(labels)}:v=0:a=1{out_label}"])

    def video_join(out_label):
        # 一般接續用 concat，有 xfade 的地方用 xfade 溶接
        steps, cur = [], "[v0]"
        for i in range(1, len(labels)):
            nxt = out_label if i == len(labels) - 1 else f"[vj{i}]"
            # 兩邊時間基準先統一（concat 輸出與單段的時間基準不同，xfade 會拒絕）
            steps.append(f"{cur}settb=1/{FPS}[p{i}];[v{i}]settb=1/{FPS}[q{i}]")
            if xfades[i] > 0:
                steps.append(f"[p{i}][q{i}]xfade=transition=fade:duration={xfades[i]:.4f}:offset={starts[i]:.4f}{nxt}")
            else:
                steps.append(f"[p{i}][q{i}]concat=n=2:v=1:a=0{nxt}")
            cur = nxt
        if len(labels) == 1:
            steps.append(f"[v0]null{out_label}")
        return ";".join(steps)

    # 常駐標題（style.title）與小字（style.note，例如版權），只出現在人物畫面
    for a, b in spans:
        if style.get("title"):
            events.append((a, b, style["title"], "Title"))
        if style.get("note"):
            events.append((a, b, style["note"], "Note"))

    ass = os.path.join(tmp, "subs.ass")
    build_ass(events, ass, style)
    if style.get("loudness") == "linear":
        # 線性響度：先只跑聲音量整支響度，再整體套一個固定增益＋限幅，逐段的大小關係原樣保留
        # （預設的 loudnorm 是動態的，會把每段各自拉回目標，gain_db 微調會被抵銷）
        achains = [ch for ch in chains if ":a]" in ch]
        probe = ";".join(achains) + ";" + audio_join("[aj]") + ";[aj]ebur128[am]"
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *inputs, "-filter_complex", probe,
                            "-map", "[am]", "-f", "null", "-"], capture_output=True, text=True)
        measured = float([l.split()[1] for l in r.stderr.splitlines() if l.strip().startswith("I:")][-1])
        afinal = (f"[ac]volume={TARGET_LUFS - measured:.2f}dB,"
                  "alimiter=limit=0.84:level=false,aresample=48000[ao]")
    else:
        afinal = "[ac]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[ao]"
    graph = ";".join(chains) + ";" + video_join("[vc]") + ";" + audio_join("[ac]") + ";" \
        f"[vc]subtitles={ass}:fontsdir={args.font}[vs];" + afinal
    if style.get("logo"):
        # style.logo：Logo 圖檔，放在標題左側，高度 logo_h，只出現在人物畫面
        inputs += ["-loop", "1", "-i", style["logo"]]
        lh = style.get("logo_h", 110)
        lx, ly = style.get("logo_x", 90), style.get("logo_y", 230)
        on = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in spans) or "0"
        graph += (f";[{n_in}:v]scale=-1:{lh},format=rgba[lg];"
                  f"[vs][lg]overlay={lx}:{ly}:shortest=1:enable='{on}'[vo]")
    else:
        graph += ";[vs]null[vo]"
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph,
         "-map", "[vo]", "-map", "[ao]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", args.out])
    print(f"{args.out}  {t0:.2f}s")


if __name__ == "__main__":
    main()
