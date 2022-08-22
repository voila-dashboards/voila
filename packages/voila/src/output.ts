import { LabWidgetManager } from '@jupyter-widgets/jupyterlab-manager';

import * as outputBase from '@jupyter-widgets/output';

import * as nbformat from '@jupyterlab/nbformat';

import { OutputAreaModel } from '@jupyterlab/outputarea';

import { KernelMessage } from '@jupyterlab/services';

/**
 * Adapt the upstream output model to Voila using a KernelWidgetManager:
 * https://github.com/jupyter-widgets/ipywidgets/blob/58adde2cfbe2f78a8ec6756d38a7c637f5e599f8/python/jupyterlab_widgets/src/output.ts#L22
 *
 * TODO: remove when https://github.com/jupyter-widgets/ipywidgets/pull/3561 (or similar) is merged and released in ipywidgets.
 */
export class OutputModel extends outputBase.OutputModel {
  defaults(): Backbone.ObjectHash {
    return { ...super.defaults(), msg_id: '', outputs: [] };
  }

  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    // The output area model is trusted since widgets are only rendered in trusted contexts.
    this._outputs = new OutputAreaModel({ trusted: true });
    this._msgHook = (msg): boolean => {
      this.add(msg);
      return false;
    };

    this.listenTo(this, 'change:msg_id', this.reset_msg_id);
    this.listenTo(this, 'change:outputs', this.setOutputs);
    this.setOutputs();
  }

  /**
   * Reset the message id.
   */
  reset_msg_id(): void {
    const kernel = this.widget_manager.kernel;
    const msgId = this.get('msg_id');
    const oldMsgId = this.previous('msg_id');

    // Clear any old handler.
    if (oldMsgId && kernel) {
      kernel.removeMessageHook(oldMsgId, this._msgHook);
    }

    // Register any new handler.
    if (msgId && kernel) {
      kernel.registerMessageHook(msgId, this._msgHook);
    }
  }

  add(msg: KernelMessage.IIOPubMessage): void {
    const msgType = msg.header.msg_type;
    switch (msgType) {
      case 'execute_result':
      case 'display_data':
      case 'stream':
      case 'error': {
        const model = msg.content as nbformat.IOutput;
        model.output_type = msgType as nbformat.OutputType;
        this._outputs.add(model);
        break;
      }
      case 'clear_output':
        this.clear_output((msg as KernelMessage.IClearOutputMsg).content.wait);
        break;
      default:
        break;
    }
    this.set('outputs', this._outputs.toJSON(), { newMessage: true });
    this.save_changes();
  }

  clear_output(wait = false): void {
    this._outputs.clear(wait);
  }

  get outputs(): OutputAreaModel {
    return this._outputs;
  }

  setOutputs(model?: any, value?: any, options?: any): void {
    if (!(options && options.newMessage)) {
      // fromJSON does not clear the existing output
      this.clear_output();
      // fromJSON does not copy the message, so we make a deep copy
      this._outputs.fromJSON(JSON.parse(JSON.stringify(this.get('outputs'))));
    }
  }

  widget_manager!: LabWidgetManager;

  private _msgHook!: (msg: KernelMessage.IIOPubMessage) => boolean;
  private _outputs!: OutputAreaModel;
}
