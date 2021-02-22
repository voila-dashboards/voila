/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import { WidgetManager as JupyterLabManager } from '@jupyter-widgets/jupyterlab-manager';
import { WidgetRenderer } from '@jupyter-widgets/jupyterlab-manager';
import { output } from '@jupyter-widgets/jupyterlab-manager';

import * as base from '@jupyter-widgets/base';
import * as controls from '@jupyter-widgets/controls';

import * as Application from '@jupyterlab/application';
import * as AppUtils from '@jupyterlab/apputils';
import * as CoreUtils from '@jupyterlab/coreutils';
import * as DocRegistry from '@jupyterlab/docregistry';
import * as OutputArea from '@jupyterlab/outputarea';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { INotebookModel } from '@jupyterlab/notebook';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import * as PhosphorWidget from '@phosphor/widgets';
import * as PhosphorSignaling from '@phosphor/signaling';
import * as PhosphorVirtualdom from '@phosphor/virtualdom';
import * as PhosphorAlgorithm from '@phosphor/algorithm';
import * as PhosphorCommands from '@phosphor/commands';
import * as PhosphorDomutils from '@phosphor/domutils';

import { MessageLoop } from '@phosphor/messaging';

import { requireLoader } from './loader';
import { batchRateMap } from './utils';
import { Widget } from '@phosphor/widgets';

if (typeof window !== 'undefined' && typeof window.define !== 'undefined') {
  window.define('@jupyter-widgets/base', base);
  window.define('@jupyter-widgets/controls', controls);
  window.define('@jupyter-widgets/output', output);

  window.define('@jupyterlab/application', Application);
  window.define('@jupyterlab/apputils', AppUtils);
  window.define('@jupyterlab/coreutils', CoreUtils);
  window.define('@jupyterlab/docregistry', DocRegistry);
  window.define('@jupyterlab/outputarea', OutputArea);

  window.define('@phosphor/widgets', PhosphorWidget);
  window.define('@phosphor/signaling', PhosphorSignaling);
  window.define('@phosphor/virtualdom', PhosphorVirtualdom);
  window.define('@phosphor/algorithm', PhosphorAlgorithm);
  window.define('@phosphor/commands', PhosphorCommands);
  window.define('@phosphor/domutils', PhosphorDomutils);
}

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/**
 * A custom widget manager to render widgets with Voila
 */
export class WidgetManager extends JupyterLabManager {
  constructor(
    context: DocumentRegistry.IContext<INotebookModel>,
    rendermime: IRenderMimeRegistry,
    settings: JupyterLabManager.Settings
  ) {
    super(context, rendermime, settings);
    rendermime.addFactory(
      {
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: options => new WidgetRenderer(options, this)
      },
      1
    );
    this._registerWidgets();
    this._loader = requireLoader;
  }

  async build_widgets(): Promise<void> {
    const models = await this._build_models();
    const tags = document.body.querySelectorAll(
      'script[type="application/vnd.jupyter.widget-view+json"]'
    );
    tags.forEach(async viewtag => {
      if (!viewtag?.parentElement) {
        return;
      }
      try {
        const widgetViewObject = JSON.parse(viewtag.innerHTML);
        const { model_id } = widgetViewObject;
        const model = models[model_id];
        const widgetel = document.createElement('div');
        viewtag.parentElement.insertBefore(widgetel, viewtag);
        // TODO: fix typing
        await this.display_model(undefined as any, model, {
          el: widgetel
        });
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
    });
  }

  async display_view(msg: any, view: any, options: any): Promise<Widget> {
    if (options.el) {
      PhosphorWidget.Widget.attach(view.pWidget, options.el);
    }
    if (view.el) {
      view.el.setAttribute('data-voila-jupyter-widget', '');
      view.el.addEventListener('jupyterWidgetResize', (e: Event) => {
        MessageLoop.postMessage(
          view.pWidget,
          PhosphorWidget.Widget.ResizeMessage.UnknownSize
        );
      });
    }
    return view.pWidget;
  }

  async loadClass(
    className: string,
    moduleName: string,
    moduleVersion: string
  ): Promise<any> {
    if (
      moduleName === '@jupyter-widgets/base' ||
      moduleName === '@jupyter-widgets/controls' ||
      moduleName === '@jupyter-widgets/output'
    ) {
      return super.loadClass(className, moduleName, moduleVersion);
    } else {
      // TODO: code duplicate from HTMLWidgetManager, consider a refactor
      return this._loader(moduleName, moduleVersion).then(module => {
        if (module[className]) {
          return module[className];
        } else {
          return Promise.reject(
            'Class ' +
              className +
              ' not found in module ' +
              moduleName +
              '@' +
              moduleVersion
          );
        }
      });
    }
  }

  restoreWidgets(notebook: INotebookModel): Promise<void> {
    return Promise.resolve();
  }

  private _registerWidgets(): void {
    this.register({
      name: '@jupyter-widgets/base',
      version: base.JUPYTER_WIDGETS_VERSION,
      exports: base as any
    });
    this.register({
      name: '@jupyter-widgets/controls',
      version: controls.JUPYTER_CONTROLS_VERSION,
      exports: controls as any
    });
    this.register({
      name: '@jupyter-widgets/output',
      version: output.OUTPUT_WIDGET_VERSION,
      exports: output as any
    });
  }

  async _build_models(): Promise<{ [key: string]: base.WidgetModel }> {
    const comm_ids = await this._get_comm_info();
    const models: { [key: string]: base.WidgetModel } = {};
    /**
     * For the classical notebook, iopub_msg_rate_limit=1000 (default)
     * And for zmq, we are affected by the default ZMQ_SNDHWM setting of 1000
     * See https://github.com/voila-dashboards/voila/issues/534 for a discussion
     */
    const maxMessagesInTransit = 100; // really save limit compared to ZMQ_SNDHWM
    const maxMessagesPerSecond = 500; // lets be on the save side, in case the kernel sends more msg'es
    const widgets_info = await Promise.all(
      batchRateMap(
        Object.keys(comm_ids),
        async comm_id => {
          const comm = await this._create_comm(this.comm_target_name, comm_id);
          return this._update_comm(comm);
        },
        { room: maxMessagesInTransit, rate: maxMessagesPerSecond }
      )
    );

    await Promise.all(
      widgets_info.map(async widget_info => {
        const state = (widget_info as any).msg.content.data.state;
        const modelPromise = this.new_model(
          {
            model_name: state._model_name,
            model_module: state._model_module,
            model_module_version: state._model_module_version,
            comm: (widget_info as any).comm
          },
          state
        );
        const model = await modelPromise;
        models[model.model_id] = model;
        return modelPromise;
      })
    );
    return models;
  }

  async _update_comm(
    comm: base.IClassicComm
  ): Promise<{ comm: base.IClassicComm; msg: any }> {
    return new Promise((resolve, reject) => {
      comm.on_msg(async msg => {
        if (msg.content.data.buffer_paths) {
          base.put_buffers(
            msg.content.data.state,
            msg.content.data.buffer_paths,
            msg.buffers
          );
        }
        if (msg.content.data.method === 'update') {
          resolve({ comm: comm, msg: msg });
        }
      });
      comm.send({ method: 'request_state' }, {});
    });
  }

  private _loader: (name: any, version: any) => Promise<any>;
}
