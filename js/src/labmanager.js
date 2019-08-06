// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import * as base from '@jupyter-widgets/base';

// We import only the version from the specific module in controls so that the
// controls code can be split and dynamically loaded in webpack.
import {
    JUPYTER_CONTROLS_VERSION
} from '@jupyter-widgets/controls/lib/version';


import { OutputArea, OutputAreaModel } from '@jupyterlab/outputarea';

import '@jupyter-widgets/base/css/index.css';
import '@jupyter-widgets/controls/css/widgets-base.css';

import {
    Widget
} from '@phosphor/widgets';

import { Signal } from '@phosphor/signaling';

import { valid } from 'semver';

import { SemVerCache } from '@jupyter-widgets/jupyterlab-manager/lib/semvercache';

import { BackboneViewWrapper } from '@jupyter-widgets/jupyterlab-manager/lib/manager';

import { output } from '@jupyter-widgets/jupyterlab-manager';

import {
    ManagerBase,
    shims,
    put_buffers,
} from '@jupyter-widgets/base';


export class VoilaManager extends ManagerBase {
    constructor(kernel, rendermime) {
        super();
        this._kernel = kernel;
        this._rendermime = rendermime;

        this._registry = new SemVerCache();

        this._restored = new Signal(this);

        // Set _handleCommOpen so `this` is captured.
        this._handleCommOpen = async (comm, msg) => {
            let oldComm = new shims.services.Comm(comm);
            await this.handle_comm_open(oldComm, msg);
        };

        kernel.statusChanged.connect((sender, args) => {
            this._handleKernelStatusChange(args);
        });

        kernel.registerCommTarget(this.comm_target_name, this._handleCommOpen);

        this._registerWidgets();

        this.restoreWidgets();

    }

    async build_widgets(rootNode) {
        rootNode = rootNode || document.body;
        const outputs = rootNode.querySelectorAll('script[type="application/x.voila-lab-output+json"]');
        for (let i = 0; i != outputs.length; ++i) {
            const node = outputs[i];
            try {
                const model = new OutputAreaModel();
                const data = JSON.parse(node.innerText);
                model.fromJSON(data.outputs);
                model.trusted = true;
                const view = new OutputArea({
                    model,
                    rendermime: this.rendermime
                });
                Widget.attach(view, node.parentNode, node);
                node.remove();
            } catch (error) {
                console.error(error);
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

    _registerWidgets() {
        this.register({
            name: '@jupyter-widgets/base',
            version: base.JUPYTER_WIDGETS_VERSION,
            exports: {
                WidgetModel: base.WidgetModel,
                WidgetView: base.WidgetView,
                DOMWidgetView: base.DOMWidgetView,
                DOMWidgetModel: base.DOMWidgetModel,
                LayoutModel: base.LayoutModel,
                LayoutView: base.LayoutView,
                StyleModel: base.StyleModel,
                StyleView: base.StyleView
            }
        });

        this.register({
            name: '@jupyter-widgets/controls',
            version: JUPYTER_CONTROLS_VERSION,
            exports: () => {
                return new Promise((resolve, reject) => {
                    resolve(import('@jupyter-widgets/controls'));
                });
            }
        });

        this.register({
            name: '@jupyter-widgets/output',
            version: output.OUTPUT_WIDGET_VERSION,
            exports: output
        });
    }


    _handleKernelStatusChange(args) {
        switch (args) {
            case 'connected':
                this.restoreWidgets();
                break;
            case 'restarting':
                this.disconnect();
                break;
            default:
        }
    }

    /**
     * Restore widgets from kernel and saved state.
     */
    async restoreWidgets() {
        await this._loadFromKernel();
        this._restored.emit();
    }

    async _loadFromKernel() {
        if (!this._kernel) {
            return;
        }
        await this._kernel.ready;
        const comm_ids = await this._get_comm_info();

        // For each comm id, create the comm, and request the state.
        const widgets_info = await Promise.all(Object.keys(comm_ids).map(async (comm_id) => {
            const comm = await this._create_comm(this.comm_target_name, comm_id);
            const update_promise = new Promise((resolve, reject) => {
                comm.on_msg((msg) => {
                    put_buffers(msg.content.data.state, msg.content.data.buffer_paths, msg.buffers);
                    // A suspected response was received, check to see if
                    // it's a state update. If so, resolve.
                    if (msg.content.data.method === 'update') {
                        resolve({
                            comm: comm,
                            msg: msg
                        });
                    }
                });
            });
            comm.send({
                method: 'request_state'
            }, this.callbacks(undefined));

            return await update_promise;
        }));

        // We put in a synchronization barrier here so that we don't have to
        // topologically sort the restored widgets. `new_model` synchronously
        // registers the widget ids before reconstructing their state
        // asynchronously, so promises to every widget reference should be available
        // by the time they are used.
        await Promise.all(widgets_info.map(async widget_info => {
            const content = widget_info.msg.content;
            await this.new_model({
                model_name: content.data.state._model_name,
                model_module: content.data.state._model_module,
                model_module_version: content.data.state._model_module_version,
                comm: widget_info.comm,
            }, content.data.state);
        }));
    }

    /**
     * Return a phosphor widget representing the view
     */
    async display_view(msg, view, options) {
        return view.pWidget || new BackboneViewWrapper(view);
    }

    /**
     * Create a comm.
     */
    async _create_comm(target_name, model_id, data, metadata, buffers) {
        let comm = this._kernel.connectToComm(target_name, model_id);
        if (data || metadata) {
            comm.open(data, metadata, buffers);
        }
        return new shims.services.Comm(comm);
    }

    /**
     * Get the currently-registered comms.
     */
    async _get_comm_info() {
        const reply = await this._kernel.requestCommInfo({
            target: this.comm_target_name
        });
        return reply.content.comms;
    }

    /**
     * Get whether the manager is disposed.
     *
     * #### Notes
     * This is a read-only property.
     */
    get isDisposed() {
        return this._kernel === null;
    }

    /**
     * Dispose the resources held by the manager.
     */
    dispose() {
        if (this.isDisposed) {
            return;
        }

        if (this._commRegistration) {
            this._commRegistration.dispose();
        }
        this._kernel = null;
    }

    /**
     * Resolve a URL relative to the current notebook location.
     */
    async resolveUrl(url) {
        const partial = await this.context.urlResolver.resolveUrl(url);
        return this.context.urlResolver.getDownloadUrl(partial);
    }

    /**
     * Load a class and return a promise to the loaded object.
     */
    async loadClass(className, moduleName, moduleVersion) {

        // Special-case the Jupyter base and controls packages. If we have just a
        // plain version, with no indication of the compatible range, prepend a ^ to
        // get all compatible versions. We may eventually apply this logic to all
        // widget modules. See issues #2006 and #2017 for more discussion.
        if ((moduleName === '@jupyter-widgets/base' ||
                moduleName === '@jupyter-widgets/controls' ||
                moduleName === '@jupyter-widgets/output') &&
            valid(moduleVersion)) {
            moduleVersion = `^${moduleVersion}`;
        }

        const mod = this._registry.get(moduleName, moduleVersion);
        if (!mod) {
            throw new Error(`Module ${moduleName}, semver range ${moduleVersion} is not registered as a widget module`);
        }
        let module;
        if (typeof mod === 'function') {
            module = await mod();
        } else {
            module = await mod;
        }
        const cls = module[className];
        if (!cls) {
            throw new Error(`Class ${className} not found in module ${moduleName}`);
        }
        return cls;
    }

    get kernel() {
        return this._kernel;
    }

    get rendermime() {
        return this._rendermime;
    }

    get context() {
        console.debug('Shimming context...');
        return {
            session: {
                kernel: this._kernel,
                kernelChanged: { connect: () => {}}
            }
        };
    }

    /**
     * A signal emitted when state is restored to the widget manager.
     *
     * #### Notes
     * This indicates that previously-unavailable widget models might be available now.
     */
    get restored() {
        return this._restored;
    }

    register(data) {
        this._registry.set(data.name, data.version, data.exports);
    }

    /**
     * Get a model
     *
     * #### Notes
     * Unlike super.get_model(), this implementation always returns a promise and
     * never returns undefined. The promise will reject if the model is not found.
     */
    async get_model(model_id) {
        const modelPromise = super.get_model(model_id);
        if (modelPromise === undefined) {
            throw new Error('widget model not found');
        }
        return modelPromise;
    }
}
