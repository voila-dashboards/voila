/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

// This is mostly copied from
// https://github.com/jupyter-widgets/ipywidgets/blob/master/packages/jupyterlab-manager/src/output.ts

import * as outputBase from '@jupyter-widgets/output';

import { DOMWidgetView, JupyterPhosphorWidget } from '@jupyter-widgets/base';

import { Panel } from '@phosphor/widgets';

import { OutputAreaModel, OutputArea } from '@jupyterlab/outputarea';

const OUTPUT_WIDGET_VERSION = outputBase.OUTPUT_WIDGET_VERSION;

export
class OutputModel extends outputBase.OutputModel {
    defaults() {
        return {
            ...super.defaults(),
            msg_id: ''
        };
    }

    initialize(attributes, options) {
        super.initialize(attributes, options)
        // The output area model is trusted since widgets are
        // only rendered in trusted contexts.
        this._outputs = new OutputAreaModel({trusted: true});
        this.listenTo(this, 'change:msg_id', this.onMsgIdChange);
        this.onMsgIdChange();
    }

    onMsgIdChange() {
        if (this._msgHook) {
            this._msgHook.dispose();
        }
        this._msgHook = null;

        const kernel = this.widget_manager.kernel;
        const msgId = this.get('msg_id');
        if (kernel && msgId) {
            this._msgHook = kernel.registerMessageHook(msgId, msg => {
                this.add(msg);
                return false;
            });
        }
    }

    add(msg) {
        const msgType = msg.header.msg_type;
        switch (msgType) {
            case 'execute_result':
            case 'display_data':
            case 'stream':
            case 'error':
                const model = msg.content;
                model.output_type = msgType;
                this._outputs.add(model);
                break;
            case 'clear_output':
                this.clear_output(msg.content.wait);
                break;
            default:
                break;
        }
    }

    clear_output(wait = false) {
        this._outputs.clear(wait);
    }

    get outputs() {
        return this._outputs;
    }
}

class JupyterPhosphorPanelWidget extends Panel {
    constructor(options) {
        const { view } = options;
        delete options.view;
        super(options);
        this._view = view;
    }

    /**
     * Process the phosphor message.
     *
     * Any custom phosphor widget used inside a Jupyter widget should override
     * the processMessage function like this.
     */
    processMessage(msg) {
        super.processMessage(msg);
        this._view.processPhosphorMessage(msg);
    }

    /**
     * Dispose the widget.
     *
     * This causes the view to be destroyed as well with 'remove'
     */
    dispose() {
        if (this.isDisposed) {
            return;
        }
        super.dispose();
        if (this._view) {
            this._view.remove();
        }
        this._view = null;
    }
}

export class OutputView extends outputBase.OutputView {

    _createElement(tagName) {
        this.pWidget = new Panel()
        return this.pWidget.node;
    }

    _setElement(el) {
        if (this.el || el !== this.pWidget.node) {
            // Boxes don't allow setting the element beyond the initial creation.
            throw new Error('Cannot reset the DOM element.');
        }

        this.el = this.pWidget.node;
    }

    /**
     * Called when view is rendered.
     */
    render() {
        super.render();
        this._outputView = new OutputArea({
            rendermime: this.model.widget_manager.renderMime,
            contentFactory: OutputArea.defaultContentFactory,
            model: this.model.outputs
        });
        this.pWidget.insertWidget(0, this._outputView);
        this.pWidget.addClass('jupyter-widgets');
        this.pWidget.addClass('widget-output');
        this.update(); // Set defaults.
    }

    remove() {
        this._outputView.dispose();
        return super.remove();
    }
}
