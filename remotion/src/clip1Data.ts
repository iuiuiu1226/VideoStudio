import plan from './clip1.json';

// clip1.json 由 work/ 的逐句腳本產生：剪點、字幕卡、動畫場景（時間皆為成片秒數）
export type Vis = {
  k: 'meter' | 'causes' | 'case' | 'split' | 'virtue' | 'veil';
  focus?: 'both' | 'fear' | 'guilt';
  title?: string;
  chips?: string[];
  tag?: string;
  at?: number[];
  arrow?: number;
  lift?: [number, number];
};
export type Scene = {o: number; e: number; vis: Vis};
export type Sub = {o: number; e: number; text: string};

export const FPS = 30;
export const SCENES = plan.scenes as Scene[];
export const SUBS = plan.subs as Sub[];
export const END_CARD_FRAMES = 120;
export const MAIN_FRAMES = Math.round(plan.total * FPS);
export const TOTAL_FRAMES = MAIN_FRAMES + END_CARD_FRAMES;
