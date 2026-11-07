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
  join：跟前一段是同一句話中間的剪接（拿掉停頓、語助詞），聲音前後交疊 0.06 秒淡入淡出，接點不會「喀」一下、背景聲不會跳。
  room：背景聲檔（同一支素材安靜處做的循環檔），pad、hold 補停頓時用它，不用完全無聲。
  rx：room 接點人聲淡出的秒數（預設 0.015）；fade_in：段落開頭淡入的秒數（預設 0.012）。
  講者前後字連在一起、沒有安靜處可切時（例如「存在｜對吧」「等於說｜我們」）用 0.03，聽起來像自然收尾／開口，不會「喀」一下。
  overlay 是疊在畫面上的透明動畫檔（例如 qtrle 含 alpha 的 .mov），從該 clip 開頭對齊，疊在字幕底下。
  style.shift_y（或 clip 的 shift_y）把畫面往下移幾個像素，頂端用鏡像模糊補：IG Reels 上方介面（含模糊底）會蓋住畫面頂端約 270 px，
  標題放在那下面（y 288 起），人物頭頂太高的影片要讓出空間。
  hold 是結尾停格的秒數（聲音補靜音），讓下一段的交叉淡化不會吃掉這段最後一個字。
  pad 是結尾多留的秒數：畫面照常往下播、聲音在 out 淡出後補靜音。講者一口氣講下去、原片沒有停頓可留時，
  用它在剪接處補一個自然的換氣（約 0.2–0.5 秒），斷點才不會太快。
  xfade 是跟前一段的交叉淡化秒數（畫面溶接）；前一段結尾要留至少這麼長的空白聲音（會被剪掉），
  這一段的聲音從自己的開頭照常播放，不會被淡掉。
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

W, H, FPS = 1080, 1920, 30
AFADE = 0.012  # 每個切點的音訊淡入淡出，避免爆音
AFADE_OUT = 0.06  # 後面補靜音（pad、hold）時，聲音收尾淡出長一點，聽起來像自然停頓
XJ = 0.03  # join：同一句話中間的剪接點，前後聲音各多拿 0.03 秒交疊淡入淡出（共 0.06 秒），接點不會「喀」一下
RX = 0.015  # room：補停頓的背景聲跟人聲交疊淡入淡出的長度（0.05 會把緊貼出點的字尾淡掉，例如「解釋」聽成「介紹」、「宇宙中」少了「中」）
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
Style: Title,{style['font']},{style.get('title_size', 50)},&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,-1,0,0,0,100,100,3,0,1,{style['outline']},{style['shadow']},{style.get('title_align', 8)},{style.get('title_margin_l', 80)},80,{style.get('title_margin', 288)},1
Style: Note,{style['font']},{style.get('note_size', 26)},&H50FFFFFF,&H50FFFFFF,&H80202020,&H00000000,0,0,0,0,100,100,2,0,1,2,0,{style.get('title_align', 8)},{style.get('title_margin_l', 80)},80,{style.get('note_margin', 346)},1
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
    ap.add_argument("-o", "--out")
    ap.add_argument("--ass-only", metavar="ASS", help="只輸出字幕檔（跟成片燒進去的完全相同）就結束，不剪片；給 tools/mosaic.py 保護字幕用")
    args = ap.parse_args()
    if not args.out and not args.ass_only:
        ap.error("需要 -o 或 --ass-only")

    specs = [json.load(open(p, encoding="utf-8")) for p in args.cutlists]
    style = specs[0]["style"]
    spec = {"clips": [c for sp in specs for c in sp["clips"]]}
    tmp = tempfile.mkdtemp()
    # 全部在同一條濾鏡鏈裡剪接：每段長度先對齊到整數影格，音訊裁成同樣長度，
    # 避免分段輸出再串接時的影格補齊與 AAC 前置延遲累積，造成字幕與音畫漂移
    inputs, chains, labels, events, t0 = [], [], [], [], 0.0
    starts, xfades, durs = [], [], []  # 每段在成片的開始時間、與前一段的交叉淡化秒數、長度
    spans = []  # 人物畫面的時間區段（字卡不放標題、Logo）
    fade_end = set()  # 這些區段的標題在結尾淡出（後面交叉淡化接片尾）
    n_in = 0
    clips = spec["clips"]

    def joins(i):
        # join：跟前一段是同一句話中間的剪接（同一支素材、前一段沒有補停頓、不是交叉淡化），聲音交疊淡入淡出
        if i == 0 or not clips[i].get("join"):
            return False
        p, c = clips[i - 1], clips[i]
        return ("card" not in p and "card" not in c and p.get("src") == c.get("src")
                and not p.get("pad") and not p.get("hold") and not c.get("xfade"))
    J = [joins(i) for i in range(len(clips))]
    xjs = []  # 每段聲音前後多拿的秒數

    for i, c in enumerate(clips):
        raw = c["dur"] if "card" in c else c["out"] - c["in"]
        dur = round(raw * FPS) / FPS
        # hold：結尾停格幾秒、聲音補靜音（下一段要交叉淡化、但這段講到最後一刻時，用來留出淡化的空白）
        body = dur
        hold = round(c.get("hold", 0.0) * FPS) / FPS
        pad = round(c.get("pad", 0.0) * FPS) / FPS
        speech = body              # 有聲音的長度（pad、hold 那段補靜音）
        body = body + pad          # 畫面實際播放的長度（pad 那段畫面照常播）
        dur = body + hold
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
            xj_in = XJ if J[i] else 0.0
            xj_out = XJ if i + 1 < len(clips) and J[i + 1] else 0.0
            if xj_in:
                inputs += ["-ss", f"{c['in'] - xj_in:.4f}", "-t", f"{dur + 0.2 + xj_in}", "-i", src]
                ai = n_in
                n_in += 1
            # room：補停頓（pad、hold）用這支素材的背景聲（循環播放），不用完全無聲；
            # 教室本來就有空氣聲，突然變全靜音再出現，聽起來很不自然
            room = None
            if c.get("room") and pad + hold > 0:
                room = c["room"] if os.path.exists(c["room"]) else os.path.join(args.src, c["room"])
                inputs += ["-stream_loop", "-1", "-i", room]
                ri = n_in
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
            # 取偶數：yuv420p 的高度要偶數，奇數會被裁成少 1 列，接起來尺寸對不上
            sy = 0 if c.get("no_overlay") else int(c.get("shift_y", style.get("shift_y", 0))) // 2 * 2
            if sy:
                # 整個畫面往下移 sy 像素：標題放在 IG 上方介面下面（見 build_ass），人物頭頂要讓出空間。
                # 底部裁掉 sy，頂端空出的窄條用最上面幾列鏡像＋模糊補上（手機上會在狀態列底下）
                vf += (f",split[sa{i}][sb{i}];[sb{i}]crop={W}:{sy}:0:0,vflip,gblur=sigma=14[st{i}];"
                       f"[sa{i}]crop={W}:{H - sy}:0:0[sm{i}];[st{i}][sm{i}]vstack")
            # 逐段把響度拉到同一基準，不同手機、不同距離錄的人聲才不會忽大忽小
            # "auto_gain": false 時不自動對齊，只用 gain_db／gain_keys（音量曲線已經算好絕對大小時用）
            lufs = measure_lufs(src, c["in"], dur) if c.get("auto_gain", True) and not args.ass_only else None
            # 降噪後的素材可能很小聲，上限放寬到 ±MAX_GAIN；"gain_db" 可逐段微調
            gain = 0.0 if lufs is None or lufs < -70 else max(-MAX_GAIN, min(MAX_GAIN, TARGET_LUFS - lufs))
            gain += c.get("gain_db", 0.0)
            # 人聲做成雙單聲道（左右相同），手機喇叭、單聲道裝置都能正常出聲；浮點運算避免補音量時破音
            # gain_keys：段落內的音量曲線 [{"t", "db"}, ...]（t 是素材秒數），補償講者離手機忽遠忽近
            ride = ""
            if "gain_keys" in c:
                gk = [{**k, "t": k["t"] - c["in"]} for k in c["gain_keys"]]
                ride = f"volume='pow(10,({lerp_expr(gk, 'db', 't')})/20)':eval=frame,"
            la = dur + xj_in + xj_out  # 這段聲音的長度（含前後交疊的部分）
            if xj_out:
                fade_out = ""
            elif room or speech >= dur:
                fade_out = f",afade=t=out:st={la - AFADE:.4f}:d={AFADE}"
            else:
                fade_out = f",afade=t=out:st={speech + xj_in - AFADE_OUT:.4f}:d={AFADE_OUT}"
            af = ("aformat=sample_fmts=fltp,pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,"
                  f"highpass=f=80,volume={gain:.2f}dB,{ride}"
                  + ("" if xj_in else f"afade=t=in:d={c.get('fade_in', AFADE)},") + "anull" + fade_out)
            for s, e, text in c.get("subs", []):
                events.append((t0 + s, t0 + min(e, dur), text, "Default"))
            # 特效字（搞笑字卡、圖示）：[開始, 結束, 文字]，時間是素材秒數；文字可含 ASS 標籤（位置、動畫）
            for s, e, text in c.get("fx", []):
                a, b = max(0.0, s - c["in"]), min(dur, e - c["in"])
                if b > a:
                    events.append((t0 + a, t0 + b, text, "Fx"))
            if c.get("no_overlay"):
                # 片尾等畫面不放標題、Logo；交叉淡化接進來時，標題在淡化開始前就淡出收掉，
                # 不然淡化那一秒標題會跟片尾的 Logo 疊在一起
                if spans and t0 < spans[-1][1]:
                    spans[-1][1] = t0
                    fade_end.add(len(spans) - 1)
            elif spans and t0 <= spans[-1][1] + 1e-6:
                spans[-1][1] = t0 + dur  # 相接或交叉淡化重疊的段落合併，標題不會重複疊兩行
            else:
                spans.append([t0, t0 + dur])
        hold_vf = f",tpad=stop_mode=clone:stop_duration={hold:.4f}" if hold > 0 else ""
        if c.get("overlay"):
            # 透明動畫疊加層（穿插的圖卡、標籤），對齊這段開頭
            inputs += ["-i", c["overlay"]]
            oi = n_in
            n_in += 1
            chains.append(f"[{vi}:v]fps={FPS},trim=duration={body:.4f},setpts=PTS-STARTPTS,{vf}{hold_vf}[b{i}]")
            chains.append(f"[{oi}:v]fps={FPS},trim=duration={dur:.4f},setpts=PTS-STARTPTS,format=rgba[o{i}]")
            chains.append(f"[b{i}][o{i}]overlay=0:0:eof_action=pass,format=yuv420p[v{i}]")
        else:
            chains.append(f"[{vi}:v]fps={FPS},trim=duration={body:.4f},setpts=PTS-STARTPTS,{vf}{hold_vf}[v{i}]")
        if "card" in c:
            xj_in = xj_out = 0.0
            room = None
            la = dur
        if room:
            # 人聲最後 RX 秒淡出、背景聲淡入疊上去（出點本來就切在安靜處，淡掉的是空氣聲，不會吃到字）；
            # "rx" 可逐段改：講者字尾直接連到下一個字、沒有安靜處可切時（例如「存在｜對吧」），淡出長一點（0.03）聽起來像自然收尾
            rx = c.get("rx", RX)
            chains.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={speech + xj_in:.4f},"
                          f"asetpts=PTS-STARTPTS,afade=t=out:st={speech + xj_in - rx:.4f}:d={rx}[s{i}]")
            dl = int(round((speech + xj_in - rx) * 1000))
            chains.append(f"[{ri}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={pad + hold + rx:.4f},"
                          f"asetpts=PTS-STARTPTS,afade=t=in:d={rx},adelay={dl}|{dl}[r{i}]")
            chains.append(f"[s{i}][r{i}]amix=inputs=2:duration=longest:normalize=0,atrim=duration={la:.4f},{af}[a{i}]")
        else:
            chains.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,"
                          f"atrim=duration={min(speech + xj_in + xj_out, la):.4f},apad,atrim=duration={la:.4f},"
                          f"asetpts=PTS-STARTPTS,{af}[a{i}]")
        xjs.append((xj_in, xj_out))
        labels.append(f"[v{i}][a{i}]")
        starts.append(t0)
        xfades.append(xf)
        durs.append(dur)
        t0 += dur

    def audio_join(out_label):
        # 下一段要交叉淡化時，這段結尾的空白聲音剪掉同樣長度，讓下一段的聲音照常從頭播放
        # join 的片段跟前一段交疊淡入淡出（各多拿 XJ 秒，交疊 2×XJ），總長度不變、畫面不受影響
        parts, steps = [], []
        for i in range(len(labels)):
            cut = xfades[i + 1] if i + 1 < len(labels) else 0.0
            lab = f"[a{i}]"
            if cut > 0:
                steps.append(f"{lab}atrim=duration={durs[i] + sum(xjs[i]) - cut:.4f},asetpts=PTS-STARTPTS[at{i}]")
                lab = f"[at{i}]"
            if J[i] and parts:
                steps.append(f"{parts[-1]}{lab}acrossfade=d={2 * XJ:.3f}:c1=tri:c2=tri[aj{i}]")
                parts[-1] = f"[aj{i}]"
            else:
                parts.append(lab)
        return ";".join(steps + ["".join(parts) + f"concat=n={len(parts)}:v=0:a=1{out_label}"])

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
    for i, (a, b) in enumerate(spans):
        fad = r"{\fad(0,400)}" if i in fade_end else ""
        if style.get("title"):
            events.append((a, b, fad + style["title"], "Title"))
        if style.get("note"):
            events.append((a, b, fad + style["note"], "Note"))

    ass = os.path.join(tmp, "subs.ass")
    build_ass(events, ass, style)
    if args.ass_only:
        shutil.copy(ass, args.ass_only)
        print(f"{args.ass_only}  {t0:.2f}s")
        return
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
