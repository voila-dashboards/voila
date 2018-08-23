
import * as base from '@jupyter-widgets/base'
import * as controls from '@jupyter-widgets/controls';
import * as pWidget from '@phosphor/widgets';
import { Signal } from '@phosphor/signaling';

import { HTMLManager } from '@jupyter-widgets/html-manager';

import * as outputWidgets from './output';
import { ShimmedComm } from './services-shim';
import { createRenderMimeRegistryWithWidgets } from './renderMime';

if (typeof window !== "undefined" && typeof window.define !== "undefined") {
  window.define("@jupyter-widgets/base", base);
  window.define("@jupyter-widgets/controls", controls);
}

export class WidgetManager extends HTMLManager {
    constructor(kernel, loader) {
        super();
        this.kernel = kernel;
        this.registerWithKernel(kernel)
        this.loader = loader;
        this.renderMime = createRenderMimeRegistryWithWidgets(this);
        this._onError = new Signal(this)
        this.build_widgets()
    }

    async build_widgets() {
        let models = await this.build_models()
        window.models = models
        let element = document.body;
        let tags = element.querySelectorAll('script[type="application/vnd.jupyter.widget-view+json"]');
        for (let i=0; i!=tags.length; ++i) {
            let viewtag = tags[i];
            let widgetViewObject = JSON.parse(viewtag.innerHTML);
            let model_id = widgetViewObject.model_id;
            let model = models[model_id]
            let prev = viewtag.previousElementSibling;
            let widgetTag = document.createElement('div');
            widgetTag.className = 'widget-subarea';
            viewtag.parentElement.insertBefore(widgetTag, viewtag);
            this.display_model(undefined, model, { el : widgetTag });
        }
    }
    async build_models() {
        let comm_ids = await this._get_comm_info()
        let models = {};
        let widgets_info = await Promise.all(Object.keys(comm_ids).map(async (comm_id) => {
            var comm = await this._create_comm(this.comm_target_name, comm_id);
            return this._update_comm(comm);
        }));
        // do the creation of the widgets in parallel
        await Promise.all(widgets_info.map(async (widget_info) => {
                let promise = this.new_model({
                    model_name: widget_info.msg.content.data.state._model_name,
                    model_module: widget_info.msg.content.data.state._model_module,
                    model_module_version: widget_info.msg.content.data.state._model_module_version,
                    comm: widget_info.comm,
                }, widget_info.msg.content.data.state);
                let model = await promise;
                models[model.model_id] = model;
                return promise;
        }));
        return models
    }

    async _update_comm(comm) {
        return new Promise(function(resolve, reject) {
            comm.on_msg(async (msg) => {
                base.put_buffers(msg.content.data.state, msg.content.data.buffer_paths, msg.buffers);
                if (msg.content.data.method === 'update') {
                    resolve({comm: comm, msg: msg})
                }
            });
            comm.send({method: 'request_state'}, {})
        })
    }

    get onError() {
        return this._onError
    }

    registerWithKernel(kernel) {
        if (this._commRegistration) {
            this._commRegistration.dispose();
        }
        this._commRegistration = kernel.registerCommTarget(
            this.comm_target_name,
            (comm, message) =>
                this.handle_comm_open(new ShimmedComm(comm), message)
        );
    }

    display_view(msg, view, options) {
        const el = options.el || this.el;
        return Promise.resolve(view).then(view => {
            pWidget.Widget.attach(view.pWidget, el);
            view.on('remove', function() {
                console.log('view removed', view);
            });
            return view;
        });
    }

    loadClass(className, moduleName, moduleVersion) {
        if (moduleName === '@jupyter-widgets/output') {
            return Promise.resolve(outputWidgets).then(module => {
                if (module[className]) {
                    return module[className];
                } else {
                    return Promise.reject(
                        `Class ${className} not found in module ${moduleName}`
                    );
                }
            })
        } else {
            return super.loadClass(className, moduleName, moduleVersion)
        }
    }

    callbacks(view) {
        const baseCallbacks = super.callbacks(view)
        return {
            ...baseCallbacks,
            iopub: { output: (msg) => this._onError.emit(msg) }
        }
    }

    _create_comm(target_name, model_id, data, metadata) {
        const comm = this.kernel.connectToComm(target_name, model_id)
        if (data || metadata ) {
            comm.open(data, metadata)
        }
        return Promise.resolve(new ShimmedComm(comm))
    }

    _get_comm_info() {
        return this.kernel.requestCommInfo({ target: this.comm_target_name})
            .then(reply => reply.content.comms)
    }
}
