import { EventManager } from '@jupyterlab/services';

/**
 * Need https://github.com/jupyterlab/jupyterlab/pull/14770 for a better mock
 *
 * @export
 * @class VoilaEventManager
 * @extends {EventManager}
 */
export class VoilaEventManager extends EventManager {
  constructor(options: EventManager.IOptions = {}) {
    super(options);
    this.dispose();
  }
}
