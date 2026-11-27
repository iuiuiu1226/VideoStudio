import {Composition} from 'remotion';
import {Clip1} from './Clip1';
import {FPS, TOTAL_FRAMES} from './clip1Data';

export const Root: React.FC = () => (
  <Composition
    id="Clip1"
    component={Clip1}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
