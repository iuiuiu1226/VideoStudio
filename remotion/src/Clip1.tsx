import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {END_CARD_FRAMES, FPS, MAIN_FRAMES, SCENES, SUBS, Vis} from './clip1Data';

const GOLD = '#f2c35b';
const GOLD_SOFT = 'rgba(242,195,91,0.55)';
const CORAL = '#ff7a59';
const FONT = "'Noto Sans CJK TC', 'Noto Sans TC', sans-serif";

// 原片右上角講者小畫面（1280x720）中，以臉為中心的方形裁切
const CAM = {x: 1105, y: 0, size: 120};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Stars: React.FC = () => {
  const frame = useCurrentFrame();
  const stars = React.useMemo(() => {
    let seed = 7;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    return Array.from({length: 110}, () => ({
      x: rnd() * 1080,
      y: rnd() * 1920,
      r: 1.2 + rnd() * 2.6,
      p: rnd() * Math.PI * 2,
      sp: 0.02 + rnd() * 0.05,
    }));
  }, []);
  return (
    <AbsoluteFill>
      {stars.map((s, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: s.x,
            top: s.y,
            width: s.r * 2,
            height: s.r * 2,
            borderRadius: '50%',
            background: '#fff',
            opacity: 0.25 + 0.5 * (0.5 + 0.5 * Math.sin(frame * s.sp + s.p)),
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

const Mountains: React.FC = () => (
  <svg width="1080" height="520" viewBox="0 0 1080 520" style={{position: 'absolute', inset: 0, opacity: 0.2}}>
    <path d="M560 520 L700 330 L760 380 L860 250 L960 340 L1080 290 L1080 520Z" fill="#8c6a3a" />
    <path d="M700 520 L820 400 L900 440 L1000 360 L1080 400 L1080 520Z" fill="#b48a4a" />
    <path d="M0 520 L90 400 L150 430 L240 330 L330 420 L420 380 L500 520Z" fill="#8c6a3a" />
  </svg>
);

const label = (size: number, color = '#fff'): React.CSSProperties => ({
  position: 'absolute',
  fontSize: size,
  fontWeight: 800,
  color,
  textShadow: '0 4px 16px rgba(0,0,0,0.6)',
  whiteSpace: 'nowrap',
  letterSpacing: 4,
});

const Hook: React.FC<{f: number}> = ({f}) => {
  const pop = interpolate(f, [0, 14], [0.2, 1], clamp);
  return (
    <>
      {[0, 1, 2].map((i) => {
        const t = ((f + i * 20) % 60) / 60;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 540 - 140,
              top: 260 - 140,
              width: 280,
              height: 280,
              borderRadius: '50%',
              border: `3px solid ${GOLD}`,
              opacity: (1 - t) * 0.6,
              transform: `scale(${1 + t * 1.3})`,
            }}
          />
        );
      })}
      <div
        style={{
          ...label(380, GOLD),
          left: 540,
          top: 260,
          transform: `translate(-50%,-50%) scale(${pop})`,
          textShadow: '0 0 50px rgba(242,195,91,0.8)',
          lineHeight: 1,
        }}
      >
        ？
      </div>
    </>
  );
};

const Meter: React.FC<{f: number; arrow?: number}> = ({f, arrow}) => {
  const X0 = 90;
  const W = 900;
  const px = (v: number) => X0 + (v / 1000) * W;
  const lineIn = interpolate(f, [0, 16], [0, 1], clamp);
  const drop = interpolate(f, [14, 34], [0, 1], clamp);
  const bounce = drop < 1 ? 0 : Math.sin((f - 34) / 5) * Math.max(0, 8 - (f - 34) * 0.25);
  const markerY = interpolate(drop, [0, 1], [90, 330]) + bounce;
  const pulse = 0.6 + 0.4 * Math.sin(f / 6);
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: X0,
          top: 310,
          width: W,
          height: 40,
          borderRadius: 20,
          background: 'linear-gradient(90deg,#b8322a,#e0822b 20%,#f2c35b 45%,#bfe3ff 100%)',
          opacity: interpolate(f, [0, 12], [0, 1], clamp),
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: X0,
          top: 310,
          width: px(200) - X0,
          height: 40,
          borderRadius: '20px 0 0 20px',
          background: 'rgba(80,0,0,0.35)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: px(200) - 2,
          top: 150 + (1 - lineIn) * 200,
          width: 4,
          height: 230 * lineIn,
          background: GOLD,
          boxShadow: '0 0 16px rgba(242,195,91,0.8)',
        }}
      />
      <div style={{...label(52, GOLD), left: px(200), top: 85, transform: 'translateX(-50%)', opacity: lineIn}}>200 臨界線</div>
      <div style={{...label(34, 'rgba(255,255,255,0.65)'), left: X0, top: 262, opacity: lineIn}}>低頻</div>
      <div style={{...label(34, 'rgba(255,255,255,0.65)'), left: X0 + W, top: 262, transform: 'translateX(-100%)', opacity: lineIn}}>高頻</div>
      <div
        style={{
          position: 'absolute',
          left: px(112.5) - 24,
          top: markerY - 24,
          width: 48,
          height: 48,
          borderRadius: '50%',
          background: CORAL,
          boxShadow: `0 0 ${40 * pulse}px ${CORAL}`,
          border: '4px solid #fff',
        }}
      />
      <div style={{...label(60, CORAL), left: px(112.5), top: 395, transform: 'translateX(-30%)', opacity: drop}}>說謊 100–125</div>
      {arrow !== undefined ? (
        <div style={{position: 'absolute', inset: 0, opacity: interpolate(f, [arrow * FPS, arrow * FPS + 10], [0, 1], clamp)}}>
          <svg width="1080" height="520" style={{position: 'absolute', inset: 0}}>
            <path d={`M ${px(200) + 150} 450 L ${px(112.5) + 30} 450`} stroke={CORAL} strokeWidth="8" fill="none" strokeDasharray="16 12" />
            <path d={`M ${px(112.5) + 30} 450 l 28 -20 l 0 40 z`} fill={CORAL} />
          </svg>
          <div style={{...label(46, CORAL), left: px(200) + 170, top: 418}}>背離正向</div>
        </div>
      ) : null}
    </>
  );
};

const Orb: React.FC<{cx: number; cy: number; text: string; color: string; on: boolean; f: number}> = ({cx, cy, text, color, on, f}) => {
  const s = on ? 1 + 0.05 * Math.sin(f / 7) : 0.88;
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - 125,
        top: cy - 125,
        width: 250,
        height: 250,
        borderRadius: '50%',
        background: `radial-gradient(circle at 35% 30%, ${color}, rgba(10,12,40,0.9) 80%)`,
        border: `5px solid ${on ? GOLD : 'rgba(255,255,255,0.25)'}`,
        boxShadow: on ? `0 0 50px ${color}` : 'none',
        opacity: on ? 1 : 0.4,
        transform: `scale(${s})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 68,
        fontWeight: 900,
        letterSpacing: 4,
        color: '#fff',
        textShadow: '0 4px 14px rgba(0,0,0,0.7)',
      }}
    >
      {text}
    </div>
  );
};

const Causes: React.FC<{f: number; focus: 'both' | 'fear' | 'guilt'}> = ({f, focus}) => {
  const appear = interpolate(f, [0, 14], [0, 1], clamp);
  const fearOn = focus !== 'guilt';
  const guiltOn = focus !== 'fear';
  const dash = (f * 3) % 40;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: appear}}>
      <svg width="1080" height="520" style={{position: 'absolute', inset: 0}}>
        <path d="M300 320 C300 400 420 400 470 425" stroke={fearOn ? GOLD : 'rgba(255,255,255,0.25)'} strokeWidth="6" fill="none" strokeDasharray="14 12" strokeDashoffset={-dash} />
        <path d="M780 320 C780 400 660 400 610 425" stroke={guiltOn ? GOLD : 'rgba(255,255,255,0.25)'} strokeWidth="6" fill="none" strokeDasharray="14 12" strokeDashoffset={-dash} />
      </svg>
      <Orb cx={300} cy={190} text="恐懼" color="#6a5acd" on={fearOn} f={f} />
      <Orb cx={780} cy={190} text="罪惡感" color="#c0392b" on={guiltOn} f={f} />
      <div
        style={{
          position: 'absolute',
          left: 540 - 140,
          top: 380,
          width: 280,
          height: 100,
          borderRadius: 50,
          border: `5px solid ${CORAL}`,
          background: 'rgba(255,122,89,0.18)',
          boxShadow: '0 0 30px rgba(255,122,89,0.45)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 62,
          fontWeight: 900,
          letterSpacing: 6,
        }}
      >
        說謊
      </div>
    </div>
  );
};

const Split: React.FC<{f: number}> = ({f}) => {
  const appear = interpolate(f, [0, 14], [0, 1], clamp);
  const d = 120 + 100 * (0.5 + 0.5 * Math.sin(f / 16));
  const jitter = Math.sin(f * 1.7) * 3;
  const circle = (cx: number, t: string): React.CSSProperties => ({
    position: 'absolute',
    left: cx - 100,
    top: 250 - 100 + jitter,
    width: 200,
    height: 200,
    borderRadius: '50%',
    border: `5px solid ${GOLD}`,
    background: 'radial-gradient(circle at 35% 30%, rgba(242,195,91,0.35), rgba(10,12,40,0.9) 80%)',
    boxShadow: '0 0 36px rgba(242,195,91,0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 100,
    fontWeight: 900,
    color: '#fff',
  });
  return (
    <div style={{position: 'absolute', inset: 0, opacity: appear}}>
      <div style={circle(540 - 100 - d, '說')}>說</div>
      <div style={circle(540 + 100 + d, '做')}>做</div>
      <svg width="1080" height="520" style={{position: 'absolute', inset: 0}}>
        <line x1={540 - d} y1={250} x2={540 + d} y2={250} stroke={CORAL} strokeWidth="6" strokeDasharray="10 16" opacity="0.9" />
      </svg>
      <div style={{...label(46, CORAL), left: 540, top: 425, transform: 'translateX(-50%)'}}>⚡ 焦慮不安</div>
    </div>
  );
};

const Sparkle: React.FC<{x: number; y: number; f: number; ph: number}> = ({x, y, f, ph}) => {
  const s = 0.5 + 0.5 * Math.sin(f / 6 + ph);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: 26,
        height: 26,
        transform: `translate(-50%,-50%) scale(${0.4 + s}) rotate(45deg)`,
        background: '#fff7d6',
        boxShadow: '0 0 18px #ffe28a',
        opacity: 0.4 + 0.6 * s,
        borderRadius: 4,
      }}
    />
  );
};

const Virtue: React.FC<{f: number}> = ({f}) => {
  const appear = interpolate(f, [0, 18], [0, 1], clamp);
  const slide = interpolate(f, [0, 22], [160, 0], clamp);
  const ring = (cx: number): React.CSSProperties => ({
    position: 'absolute',
    left: cx - 170,
    top: 250 - 170,
    width: 340,
    height: 340,
    borderRadius: '50%',
    border: `6px solid ${GOLD}`,
    background: 'radial-gradient(circle, rgba(242,195,91,0.22), rgba(242,195,91,0.04) 70%)',
    boxShadow: '0 0 40px rgba(242,195,91,0.45)',
  });
  return (
    <div style={{position: 'absolute', inset: 0, opacity: appear}}>
      <div style={ring(540 - 95 - slide * 0.4)} />
      <div style={ring(540 + 95 + slide * 0.4)} />
      <div style={{...label(70, '#fff'), left: 540 - 215, top: 250, transform: 'translate(-50%,-50%)'}}>誠信</div>
      <div style={{...label(70, '#fff'), left: 540 + 215, top: 250, transform: 'translate(-50%,-50%)'}}>真實</div>
      <Sparkle x={540} y={250} f={f} ph={0} />
      <Sparkle x={420} y={130} f={f} ph={2} />
      <Sparkle x={660} y={380} f={f} ph={4} />
      <Sparkle x={700} y={120} f={f} ph={1} />
      <Sparkle x={380} y={390} f={f} ph={3} />
    </div>
  );
};

const Veil: React.FC<{f: number; total: number; lift: [number, number]; tag?: string}> = ({f, total, lift, tag}) => {
  const p = interpolate(f, [0, total], lift, clamp);
  const glow = 0.35 + 0.65 * p;
  const sway = Math.sin(f / 18) * 14;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 540 - 165,
          top: 260 - 165,
          width: 330,
          height: 330,
          borderRadius: '50%',
          background: `radial-gradient(circle at 40% 35%, rgba(255,236,170,${0.5 + 0.5 * p}), rgba(242,195,91,${0.25 + 0.35 * p}) 55%, rgba(10,12,40,0.9) 100%)`,
          boxShadow: `0 0 ${30 + 90 * glow}px rgba(242,195,91,${0.3 + 0.6 * glow})`,
          border: `5px solid rgba(242,195,91,${0.4 + 0.6 * p})`,
        }}
      />
      <div style={{...label(64, '#fff'), left: 540, top: 260, transform: 'translate(-50%,-50%)', opacity: 0.55 + 0.45 * p}}>真實的自己</div>
      {[0, 1].map((i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: 250 + i * 30 + sway * (i ? -1 : 1),
            top: 70 + i * 24 - p * 460,
            width: 580 - i * 60,
            height: 380,
            borderRadius: 40,
            background: 'linear-gradient(180deg, rgba(210,225,255,0.62), rgba(120,150,225,0.38))',
            filter: 'blur(5px)',
            opacity: (1 - p) * (0.95 - i * 0.2),
          }}
        />
      ))}
      <div style={{...label(52, GOLD), left: 540, top: 440, transform: 'translateX(-50%)', opacity: interpolate(p, [0.85, 1], [0, 1], clamp)}}>輕鬆 · 平靜</div>
      {tag ? (
        <div style={{...label(46, GOLD), left: 540, top: 28, transform: 'translateX(-50%)', padding: '6px 30px', border: `3px solid ${GOLD}`, borderRadius: 999}}>{tag}</div>
      ) : null}
    </>
  );
};

const Case: React.FC<{f: number; vis: Vis}> = ({f, vis}) => {
  const at = vis.at ?? [0, 0, 0, 0];
  const chips = vis.chips ?? [];
  const head = interpolate(f, [0, 12], [0, 1], clamp);
  const reveal = (i: number) => interpolate(f, [at[i] * FPS, at[i] * FPS + 10], [0, 1], clamp);
  const tagIn = reveal(3);
  return (
    <>
      <div style={{...label(70, GOLD), left: 60, top: 22, opacity: head, padding: '4px 34px', border: `4px solid ${GOLD}`, borderRadius: 16, boxShadow: '0 0 24px rgba(242,195,91,0.4)'}}>{vis.title}</div>
      {chips.map((c, i) => {
        const r = reveal(i);
        const last = i === chips.length - 1;
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: 60,
                top: 140 + i * 125,
                width: 590,
                height: 96,
                borderRadius: 24,
                border: `3px solid ${last ? CORAL : 'rgba(255,255,255,0.4)'}`,
                background: last ? 'rgba(255,122,89,0.16)' : 'rgba(255,255,255,0.07)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 52,
                fontWeight: 800,
                letterSpacing: 3,
                opacity: r,
                transform: `translateX(${(1 - r) * -50}px)`,
              }}
            >
              {c}
            </div>
            {i < chips.length - 1 ? (
              <div style={{...label(34, GOLD), left: 340, top: 236 + i * 125, opacity: reveal(i + 1)}}>▼</div>
            ) : null}
          </React.Fragment>
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: 730,
          top: 160,
          width: 280,
          height: 280,
          borderRadius: '50%',
          background: `radial-gradient(circle at 35% 30%, ${CORAL}, rgba(10,12,40,0.92) 80%)`,
          border: `5px solid ${GOLD}`,
          boxShadow: `0 0 ${50 * tagIn}px ${CORAL}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 66,
          fontWeight: 900,
          letterSpacing: 4,
          opacity: tagIn,
          transform: `scale(${0.6 + 0.4 * tagIn})`,
          textShadow: '0 4px 14px rgba(0,0,0,0.7)',
        }}
      >
        {vis.tag}
      </div>
    </>
  );
};

const Visual: React.FC<{vis: Vis; f: number; total: number}> = ({vis, f, total}) => (
  <div
    style={{
      position: 'absolute',
      left: 0,
      top: 610,
      width: 1080,
      height: 520,
      background: 'linear-gradient(90deg, rgba(36,24,12,0.55), rgba(14,24,56,0.7) 55%, rgba(30,22,10,0.5))',
      borderTop: `2px solid ${GOLD_SOFT}`,
      borderBottom: `2px solid ${GOLD_SOFT}`,
      overflow: 'hidden',
      fontFamily: FONT,
    }}
  >
    <Mountains />
    {vis.k === 'meter' && <Meter f={f} arrow={vis.arrow} />}
    {vis.k === 'case' && <Case f={f} vis={vis} />}
    {vis.k === 'causes' && <Causes f={f} focus={vis.focus ?? 'both'} />}
    {vis.k === 'split' && <Split f={f} />}
    {vis.k === 'virtue' && <Virtue f={f} />}
    {vis.k === 'veil' && <Veil f={f} total={total} lift={vis.lift ?? [0, 0]} tag={vis.tag} />}
  </div>
);

export const Clip1: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;

  const scene = SCENES.find((sc) => t >= sc.o - 1e-6 && t < sc.e - 1e-6) ?? SCENES[SCENES.length - 1];
  const localFrames = Math.max(0, Math.round((t - scene.o) * FPS));
  const segFrames = Math.max(1, Math.round((scene.e - scene.o) * FPS));

  const sub = SUBS.find((x) => t >= x.o - 1e-6 && t < x.e - 1e-6);
  const subOp = sub ? interpolate(t - sub.o, [0, 0.12], [0, 1], clamp) : 0;

  const titleIn = interpolate(frame, [0, 16], [0, 1], clamp);
  const titleY = interpolate(frame, [0, 16], [40, 0], clamp);
  const glow = 0.55 + 0.45 * Math.sin(frame / 9);
  const endLocal = frame - MAIN_FRAMES;

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 50% 20%, #101a3e 0%, #080c22 55%, #04061a 100%)',
        fontFamily: FONT,
        color: '#fff',
      }}
    >
      <Stars />

      <div
        style={{
          position: 'absolute',
          left: 64,
          top: 118,
          padding: '14px 32px',
          border: `2px solid ${GOLD_SOFT}`,
          borderRadius: 999,
          fontSize: 36,
          fontWeight: 600,
          color: GOLD,
          background: 'rgba(20,24,50,0.6)',
        }}
      >
        拉低能量的五種行為・第 1 種
      </div>

      <div
        style={{
          position: 'absolute',
          left: 64,
          top: 232,
          opacity: endLocal >= 0 ? 0 : titleIn,
          transform: `translateY(${titleY}px)`,
          fontSize: 98,
          fontWeight: 900,
          lineHeight: 1.22,
          textShadow: '0 6px 24px rgba(0,0,0,0.55)',
        }}
      >
        說謊，為什麼會
        <br />
        <span style={{color: GOLD, textShadow: `0 0 ${24 * glow}px rgba(242,195,91,0.7)`}}>拉低能量</span>？
      </div>

      <Sequence from={0} durationInFrames={MAIN_FRAMES}>
        <div
          style={{
            position: 'absolute',
            right: 56,
            top: 190,
            width: 250,
            height: 250,
            borderRadius: '50%',
            overflow: 'hidden',
            border: `7px solid ${GOLD}`,
            boxShadow: '0 0 36px rgba(242,195,91,0.5)',
            background: '#000',
          }}
        >
          <OffthreadVideo
            src={staticFile('clip1_src.mp4')}
            style={{
              position: 'absolute',
              width: 1280 * (250 / CAM.size),
              height: 720 * (250 / CAM.size),
              left: -CAM.x * (250 / CAM.size),
              top: -CAM.y * (250 / CAM.size),
              maxWidth: 'none',
            }}
          />
        </div>

        <Visual vis={scene.vis} f={localFrames} total={segFrames} />

        {/* 講者字幕：半透明卡片，與中間圖像分開 */}
        {sub ? (
          <div style={{position: 'absolute', left: 0, width: 1080, top: 1190, display: 'flex', justifyContent: 'center', opacity: subOp}}>
            <div
              style={{
                textAlign: 'center',
                fontSize: 44,
                fontWeight: 600,
                lineHeight: 1.5,
                letterSpacing: 1,
                whiteSpace: 'pre-line',
                textShadow: '0 2px 10px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.9)',
              }}
            >
              {sub.text}
            </div>
          </div>
        ) : null}
      </Sequence>

      {endLocal >= 0 ? (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{opacity: interpolate(endLocal, [0, 14], [0, 1], clamp), textAlign: 'center', textShadow: '0 6px 24px rgba(0,0,0,0.6)'}}>
            <div style={{fontSize: 84, fontWeight: 900, lineHeight: 1.3}}>
              拉低能量的<span style={{color: GOLD}}>五種行為</span>
            </div>
            <div style={{marginTop: 50, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
              {['說謊', '貪小便宜', '講話損人', '高傲自傲', '疑心'].map((t, i) => {
                const r = interpolate(endLocal, [10 + i * 6, 22 + i * 6], [0, 1], clamp);
                const first = i === 0;
                return (
                  <div
                    key={t}
                    style={{
                      opacity: r,
                      transform: `translateY(${(1 - r) * 24}px)`,
                      minWidth: 520,
                      padding: '10px 36px',
                      borderRadius: 18,
                      fontSize: 62,
                      fontWeight: 800,
                      letterSpacing: 6,
                      color: first ? GOLD : '#fff',
                      border: first ? `4px solid ${GOLD}` : '3px solid rgba(255,255,255,0.3)',
                      background: first ? 'rgba(242,195,91,0.12)' : 'rgba(255,255,255,0.05)',
                      boxShadow: first ? '0 0 28px rgba(242,195,91,0.45)' : undefined,
                    }}
                  >
                    {t}
                  </div>
                );
              })}
            </div>
            <div style={{marginTop: 54, fontSize: 80, fontWeight: 900, color: GOLD, opacity: interpolate(endLocal, [50, 64], [0, 1], clamp), textShadow: '0 0 30px rgba(242,195,91,0.6)'}}>
              你中了幾個？
            </div>
            <div
              style={{
                display: 'inline-block',
                marginTop: 56,
                padding: '16px 40px',
                border: `3px solid ${GOLD}`,
                borderRadius: 999,
                fontSize: 40,
                fontWeight: 700,
                color: GOLD,
                background: 'rgba(20,24,50,0.6)',
                opacity: interpolate(endLocal, [64, 78], [0, 1], clamp),
              }}
            >
              完整直播｜YouTube 第七感宇宙智慧學
            </div>
          </div>
        </AbsoluteFill>
      ) : null}

      <div
        style={{
          position: 'absolute',
          left: 0,
          width: 1080,
          top: 1560,
          opacity: endLocal >= 0 ? 0 : 1,
          textAlign: 'center',
          fontSize: 38,
          fontWeight: 600,
          letterSpacing: 2,
          color: 'rgba(255,255,255,0.55)',
        }}
      >
        完整直播｜YouTube 第七感宇宙智慧學
      </div>
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 6, width: (frame / (MAIN_FRAMES + END_CARD_FRAMES)) * 1080, background: GOLD}} />
    </AbsoluteFill>
  );
};
