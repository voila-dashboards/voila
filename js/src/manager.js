/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

import { RenderMimeRegistry, standardRendererFactories } from '@jupyterlab/rendermime';
import { requireLoader } from '@jupyter-widgets/html-manager';
import { WidgetManager as JupyterLabManager } from '@jupyter-widgets/jupyterlab-manager';
import { WidgetRenderer } from '@jupyter-widgets/jupyterlab-manager';
import { output } from '@jupyter-widgets/jupyterlab-manager';
import * as base from '@jupyter-widgets/base';
import * as controls from '@jupyter-widgets/controls';
import * as PhosphorWidget from '@phosphor/widgets';

if (typeof window !== "undefined" && typeof window.define !== "undefined") {
    window.define("@jupyter-widgets/base", base);
    window.define("@jupyter-widgets/controls", controls);
    window.define("@jupyter-widgets/output", output);
    window.define("@phosphor/widgets", PhosphorWidget);
  }

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

export class WidgetManager extends JupyterLabManager {

    constructor(kernel) {
        const context = createContext(kernel);
        const settings = createSettings();
        const rendermime = new RenderMimeRegistry({
            initialFactories: standardRendererFactories
        });
        super(context, rendermime, settings);
        rendermime.addFactory({
            safe: false,
            mimeTypes: [WIDGET_MIMETYPE],
            createRenderer: options => new WidgetRenderer(options, this)
        }, 1);
        this._registerWidgets();
        this.loader = requireLoader;
    }

    async build_widgets() {
        const models = await this._build_models();
        const tags = document.body.querySelectorAll('script[type="application/vnd.jupyter.widget-view+json"]');
        for (let i=0; i!=tags.length; ++i) {
            try {
                const viewtag = tags[i];
                const widgetViewObject = JSON.parse(viewtag.innerHTML);
                const { model_id } = widgetViewObject;
                const model = models[model_id];
                const widgetel = document.createElement('div');
                viewtag.parentElement.insertBefore(widgetel, viewtag);
                const view = await this.display_model(undefined, model, { el : widgetel });
            } catch (error) {
               // Each widget view tag rendering is wrapped with a try-catch statement.
               //
               // This fixes issues with widget models that are explicitely "closed"
               // but are still referred to in a previous cell output.
               // Without the try-catch statement, this error interupts the loop and
               // prevents the rendering of further cells.
               //
               // This workaround may not be necessary anymore with templates that make use
               // of progressive rendering.
            }
        }
    }

    display_view(msg, view, options) {
        if (options.el) {
            PhosphorWidget.Widget.attach(view.pWidget, options.el);
        }
        return view.pWidget;
    }

    async loadClass(className, moduleName, moduleVersion) {
        if (
            moduleName === '@jupyter-widgets/base' ||
            moduleName === '@jupyter-widgets/controls' ||
            moduleName === '@jupyter-widgets/output'
        ) {
            return super.loadClass(className, moduleName, moduleVersion);
        }
        else {
            // TODO: code duplicate from HTMLWidgetManager, consider a refactor
            return this.loader(moduleName, moduleVersion).then((module) => {
                if (module[className]) {
                    return module[className];
                }
                else {
                    return Promise.reject("Class " + className + " not found in module " + moduleName + "@" + moduleVersion);
                }
            })
        }
    }

    restoreWidgets(notebook) {
    }

    _registerWidgets() {
        this.register({
            name: '@jupyter-widgets/base',
            version: base.JUPYTER_WIDGETS_VERSION,
            exports: base
        });
        this.register({
            name: '@jupyter-widgets/controls',
            version: controls.JUPYTER_CONTROLS_VERSION,
            exports: controls
        });
        this.register({
            name: '@jupyter-widgets/output',
            version: output.OUTPUT_WIDGET_VERSION,
            exports: output
        });
    }

    async _build_models() {
        const comm_ids = await this._get_comm_info();
        const models = {};
        const widgets_info = await Promise.all(Object.keys(comm_ids).map(async (comm_id) => {
            const comm = await this._create_comm(this.comm_target_name, comm_id);
            return this._update_comm(comm);
        }));

        await Promise.all(widgets_info.map(async (widget_info) => {
            const state = widget_info.msg.content.data.state;
            const modelPromise = this.new_model({
                    model_name: state._model_name,
                    model_module: state._model_module,
                    model_module_version: state._model_module_version,
                    comm: widget_info.comm,
                },
                state
            );
            const model = await modelPromise;
            models[model.model_id] = model;
            return modelPromise;
        }));
        return models;
    }

    async _update_comm(comm) {
        return new Promise(function(resolve, reject) {
            comm.on_msg(async (msg) => {
                base.put_buffers(msg.content.data.state, msg.content.data.buffer_paths, msg.buffers);
                if (msg.content.data.method === 'update') {
                    resolve({comm: comm, msg: msg});
                }
            });
            comm.send({method: 'request_state'}, {});
        });
    }

}

function createContext(kernel) {
    return {
        session: {
            kernel,
            kernelChanged: {
                connect: () => {}
            },
            statusChanged: {
                connect: () => {}
            },
        },
        saveState: {
            connect: () => {}
        },
    };
}

function createSettings() {
    return {
        saveState: false
    };
}
