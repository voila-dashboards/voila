import { PromiseDelegate } from '@lumino/coreutils';
import { WidgetModel } from '@jupyter-widgets/base';
import { WidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { ISignal, Signal } from '@lumino/signaling';
import { INotebookModel } from '@jupyterlab/notebook';
import { Widget } from '@lumino/widgets';
import { MessageLoop } from '@lumino/messaging';

export class VoilaWidgetManager extends WidgetManager {
  register_model(model_id: string, modelPromise: Promise<WidgetModel>): void {
    super.register_model(model_id, modelPromise);
    this._registeredModels.add(model_id);
    this._modelRegistered.emit(model_id);
  }

  get kernel() {
    return this.context.sessionContext.session?.kernel;
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

  async _loadFromKernel(): Promise<void> {
    await super._loadFromKernel();

    this._loadedFromKernel.resolve();
  }

  get loadedModelsFromKernel(): Promise<void> {
    return this._loadedFromKernel.promise;
  }

  async display_view(msg: any, view: any, options: any): Promise<Widget> {
    if (options.el) {
      Widget.attach(view.pWidget, options.el);
    }
    if (view.el) {
      view.el.setAttribute('data-voila-jupyter-widget', '');
      view.el.addEventListener('jupyterWidgetResize', (e: Event) => {
        MessageLoop.postMessage(view.pWidget, Widget.ResizeMessage.UnknownSize);
      });
    }
    return view.pWidget;
  }

  restoreWidgets(notebook: INotebookModel): Promise<void> {
    return Promise.resolve();
  }

  private _loadedFromKernel: PromiseDelegate<void> = new PromiseDelegate();
  private _modelRegistered = new Signal<VoilaWidgetManager, string>(this);
  private _registeredModels = new Set<string>();
}
