import { BaseManager, KernelSpec } from '@jupyterlab/services';
import { ISpecModels } from '@jupyterlab/services/lib/kernelspec/restapi';
import { ISignal, Signal } from '@lumino/signaling';

export class VoilaKernelSpecManager
  extends BaseManager
  implements KernelSpec.IManager
{
  specsChanged: ISignal<this, ISpecModels> = new Signal(this);
  connectionFailure: ISignal<this, Error> = new Signal(this);
  readonly specs: ISpecModels | null = null;

  refreshSpecs(): Promise<void> {
    return Promise.resolve();
  }

  get isReady(): boolean {
    return true;
  }

  get ready(): Promise<void> {
    return Promise.resolve();
  }
}
