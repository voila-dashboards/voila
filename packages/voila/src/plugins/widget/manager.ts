import { WidgetModel } from '@jupyter-widgets/base';
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { ISignal, Signal } from '@lumino/signaling';

export class VoilaWidgetManager extends KernelWidgetManager {
  register_model(model_id: string, modelPromise: Promise<WidgetModel>): void {
    super.register_model(model_id, modelPromise);
    this._registeredModels.add(model_id);
    this._modelRegistered.emit(model_id);
  }
  get registeredModels(): ReadonlySet<string> {
    return this._registeredModels;
  }
  get modelRegistered(): ISignal<VoilaWidgetManager, string> {
    return this._modelRegistered;
  }
  removeRegisteredModel(modelId: string) {
    this._registeredModels.delete(modelId);
  }
  private _modelRegistered = new Signal<VoilaWidgetManager, string>(this);
  private _registeredModels = new Set<string>();
}
