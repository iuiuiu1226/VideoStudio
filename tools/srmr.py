"""回音多寡指標：簡化版 SRMR（Falk 2010，語音對殘響調變能量比），越高＝回音越少。
不受噪音門影響（看的是講話中的調變），可以比較同一段素材不同處理版本。
用法：python3 tools/srmr.py 影片1.mp4 影片2.mp4 …（只看 0–54 秒，要改就改 load 的 a、b）
課堂精華 VOL.02 實測：原音 3.4、v3 6.4、v4 6.9、v5 6.2、v6 7.1（吃字）、v7 7.2"""
import subprocess, sys, numpy as np
from scipy.signal import gammatone, lfilter, hilbert, butter, sosfilt, resample_poly
def load(f, a=0, b=54):
    raw = subprocess.run(["ffmpeg","-v","error","-ss",str(a),"-t",str(b-a),"-i",f,"-vn","-ac","1","-ar","16000","-f","s16le","-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768
def erb_space(lo, hi, n):
    e = lambda f: 21.4*np.log10(1+0.00437*f); ie = lambda x: (10**(x/21.4)-1)/0.00437
    return ie(np.linspace(e(lo), e(hi), n))
def srmr(y, fs=16000):
    y = y / (np.sqrt(np.mean(y**2)) + 1e-12)
    cfs = erb_space(125, 6000, 23)
    mcf = np.geomspace(4, 128, 8)
    E = np.zeros((23, 8))
    for i, cf in enumerate(cfs):
        b, a = gammatone(cf, "iir", fs=fs)
        env = np.abs(hilbert(lfilter(b, a, y)))
        env = resample_poly(env, 1, 40)          # 400 Hz
        fe = 400
        for j, mc in enumerate(mcf):
            bw = mc / 2; lo, hi = max(mc - bw/2, 0.5), min(mc + bw/2, fe/2 - 1)
            sos = butter(2, [lo, hi], btype="band", fs=fe, output="sos")
            E[i, j] = np.mean(sosfilt(sos, env) ** 2)
    return E[:, :4].sum() / E[:, 4:].sum()
for f in sys.argv[1:]:
    print(f"{f.split('VOL02_')[-1]:24s} SRMR {srmr(load(f)):.2f}", flush=True)
