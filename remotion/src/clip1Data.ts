// 時間皆為原片（70 分鐘直播）的秒數；clip1_src.mp4 由這些片段依序接成
export type Vis =
  | {k: 'hook'}
  | {k: 'meter'}
  | {k: 'causes'; focus: 'both' | 'fear' | 'guilt'}
  | {k: 'split'}
  | {k: 'virtue'}
  | {k: 'veil'; lift: [number, number]}; // 薄紗掀開的程度，片段開始→結束（0–1）
export type Seg = {s: number; e: number; vis: Vis};
export type Sub = {s: number; e: number; text: string};

export const SEGS: Seg[] = [
  {s: 690.6, e: 697.6, vis: {k: 'hook'}},
  {s: 699.6, e: 705.0, vis: {k: 'meter'}},
  {s: 710.6, e: 717.6, vis: {k: 'causes', focus: 'both'}},
  {s: 718.0, e: 732.6, vis: {k: 'causes', focus: 'fear'}},
  {s: 738.1, e: 751.1, vis: {k: 'causes', focus: 'guilt'}},
  {s: 793.1, e: 818.5, vis: {k: 'split'}},
  {s: 822.0, e: 832.5, vis: {k: 'virtue'}},
  {s: 833.0, e: 861.0, vis: {k: 'veil', lift: [0, 0]}},
  {s: 866.0, e: 871.0, vis: {k: 'veil', lift: [0, 0]}},
  {s: 876.0, e: 882.2, vis: {k: 'veil', lift: [0, 0.3]}},
  {s: 884.4, e: 891.4, vis: {k: 'veil', lift: [0.3, 0.55]}},
  {s: 891.5, e: 911.0, vis: {k: 'veil', lift: [0.55, 0.85]}},
  {s: 912.5, e: 925.0, vis: {k: 'veil', lift: [0.85, 1]}},
];

export const SUBS: Sub[] = [
  {s: 690.6, e: 697.6, text: '但是我們不知道為什麼說謊是不好的，\n甚至也不太理解怎麼用能量去對照'},
  {s: 699.6, e: 705.0, text: '說謊的意識能量分值，\n大約在 100 到 125 分左右'},
  {s: 710.6, e: 717.6, text: '為什麼會想說謊？它的動力來自於怕，\n就是所謂的恐懼與罪惡感'},
  {s: 718.0, e: 724.0, text: '比方說，小孩子偷吃零食，\n怕被媽媽知道'},
  {s: 724.0, e: 732.6, text: '媽媽問：零食去哪了？\n小孩因為怕，進而說謊'},
  {s: 738.1, e: 747.1, text: '再比方男女朋友，\n其中一方去跟別人約會，不跟另一半講'},
  {s: 747.1, e: 751.1, text: '還騙對方，\n這是一種罪惡感'},
  {s: 793.1, e: 800.4, text: '說謊的時候，\n內在是沒有言行合一的'},
  {s: 800.4, e: 808.4, text: '為了掩蓋謊言，內在會\n鬼鬼祟祟、偷偷摸摸'},
  {s: 808.4, e: 818.5, text: '甚至焦慮不安，也會影響\n人與人之間真實的連結'},
  {s: 822.0, e: 832.5, text: '說謊的正向狀態是什麼？\n是誠信與真實'},
  {s: 833.0, e: 841.0, text: '像我之前工作的時候，\n有些人會問我是哪裡人'},
  {s: 841.0, e: 852.0, text: '因為我做的是線上網路工作，\n帶著一層薄紗，不想透露太多'},
  {s: 852.0, e: 861.0, text: '所以我就缺乏了\n誠信與真實的部分'},
  {s: 866.0, e: 871.0, text: '內心就會有一點，\n沒有那麼做自己'},
  {s: 876.0, e: 882.2, text: '但是當我學了能量學之後，\n我發現原來我們人'},
  {s: 884.4, e: 891.4, text: '往真誠的角度越走，\n你的能量會越高'},
  {s: 891.5, e: 898.5, text: '當我知道這個道理，\n我一直告訴自己'},
  {s: 898.5, e: 905.5, text: '不要把身邊的任何人、任何事，\n當成假想敵'},
  {s: 905.5, e: 911.0, text: '我盡量用誠信與真誠的角度，\n跟對方相處'},
  {s: 912.5, e: 919.5, text: '現在我的工作就是用這樣的方式，\n不需要花太多心思去掩蓋自己'},
  {s: 919.5, e: 925.0, text: '現在工作的時候，\n內心也獲得很大的輕鬆與平靜'},
];

export const FPS = 30;
export const CLIP_SECONDS = SEGS.reduce((a, g) => a + (g.e - g.s), 0);
export const END_CARD_FRAMES = 90;
export const MAIN_FRAMES = Math.round(CLIP_SECONDS * FPS);
export const TOTAL_FRAMES = MAIN_FRAMES + END_CARD_FRAMES;

// 把原片秒數換算成成片上的秒數
export const srcToOut = (src: number): number => {
  let acc = 0;
  for (const g of SEGS) {
    if (src >= g.s - 1e-6 && src <= g.e + 1e-6) return acc + (src - g.s);
    acc += g.e - g.s;
  }
  throw new Error('src time not in any segment: ' + src);
};
