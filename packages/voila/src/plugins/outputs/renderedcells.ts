import { Message } from '@lumino/messaging';
import { Widget } from '@lumino/widgets';

/**
 * Wrapper widget of rendered cells, this class converts the Lumino resize
 * message to a window event. It helps fix the zero-heigh issue of some
 * widgets
 *
 */
export class RenderedCells extends Widget {
  processMessage(msg: Message): void {
    super.processMessage(msg);
    switch (msg.type) {
      case 'resize':
        window.dispatchEvent(new Event('resize'));
        break;

      default:
        break;
    }
  }
}
