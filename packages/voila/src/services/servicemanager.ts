import { ServiceManager } from '@jupyterlab/services';
import { VoilaEventManager } from './event';
import { VoilaUserManager } from './user';
import { VoilaKernelSpecManager } from './kernelspec';

const alwaysTrue = () => true;

/**
 * A custom service manager to disable non used services.
 *
 * @export
 * @class VoilaServiceManager
 * @extends {ServiceManager}
 */
export class VoilaServiceManager extends ServiceManager {
  constructor(options?: Partial<ServiceManager.IOptions>) {
    super({
      standby: options?.standby ?? alwaysTrue,
      kernelspecs: options?.kernelspecs ?? new VoilaKernelSpecManager({}),
      events: options?.events ?? new VoilaEventManager(),
      user: options?.user ?? new VoilaUserManager({})
    });
  }
}
