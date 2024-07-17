/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import $ from "jquery";
import 'jquery-ui/ui/widgets/slider';

import {
  WidgetManager as JupyterLabManager,
  WidgetRenderer
} from '@jupyter-widgets/jupyterlab-manager';

import * as Application from '@jupyterlab/application';
import * as AppUtils from '@jupyterlab/apputils';
import * as CoreUtils from '@jupyterlab/coreutils';
import * as DocRegistry from '@jupyterlab/docregistry';
import * as OutputArea from '@jupyterlab/outputarea';

import { DocumentRegistry } from '@jupyterlab/docregistry';
import { INotebookModel } from '@jupyterlab/notebook';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import * as LuminoWidget from '@lumino/widgets';
import * as LuminoSignaling from '@lumino/signaling';
import * as LuminoVirtualdom from '@lumino/virtualdom';
import * as LuminoAlgorithm from '@lumino/algorithm';
import * as LuminoCommands from '@lumino/commands';
import * as LuminoDomutils from '@lumino/domutils';

import { MessageLoop } from '@lumino/messaging';

import { Widget } from '@lumino/widgets';

import { requireLoader } from './loader';

if (typeof window !== 'undefined' && typeof window.define !== 'undefined') {
  window.define('jquery', $);

  window.define('@jupyterlab/application', Application);
  window.define('@jupyterlab/apputils', AppUtils);
  window.define('@jupyterlab/coreutils', CoreUtils);
  window.define('@jupyterlab/docregistry', DocRegistry);
  window.define('@jupyterlab/outputarea', OutputArea);

  window.define('@phosphor/widgets', LuminoWidget);
  window.define('@phosphor/signaling', LuminoSignaling);
  window.define('@phosphor/virtualdom', LuminoVirtualdom);
  window.define('@phosphor/algorithm', LuminoAlgorithm);
  window.define('@phosphor/commands', LuminoCommands);
  window.define('@phosphor/domutils', LuminoDomutils);

  window.define('@lumino/widgets', LuminoWidget);
  window.define('@lumino/signaling', LuminoSignaling);
  window.define('@lumino/virtualdom', LuminoVirtualdom);
  window.define('@lumino/algorithm', LuminoAlgorithm);
  window.define('@lumino/commands', LuminoCommands);
  window.define('@lumino/domutils', LuminoDomutils);
}

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/**
 * Time (in ms) after which we consider the control comm target not responding.
 */
export const CONTROL_COMM_TIMEOUT = 4000;

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
    await this._loadFromKernel();
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
        const model = await this.get_model(model_id);
        const widgetel = document.createElement('div');
        viewtag.parentElement.insertBefore(widgetel, viewtag);
        const view = await this.create_view(model);
        // TODO: fix typing
        await this.display_view(undefined as any, view, {
          el: widgetel
        });
      } catch (error) {
        // Each widget view tag rendering is wrapped with a try-catch statement.
        //
        // This fixes issues with widget models that are explicitly "closed"
        // but are still referred to in a previous cell output.
        // Without the try-catch statement, this error interrupts the loop and
        // prevents the rendering of further cells.
        //
        // This workaround may not be necessary anymore with templates that make use
        // of progressive rendering.
        console.error('Something went wrong', error);
      }
    });
  }

  async display_view(msg: any, view: any, options: any): Promise<Widget> {
    if (options.el) {
      LuminoWidget.Widget.attach(view.luminoWidget || view.pWidget, options.el);
    }
    if (view.el) {
      view.el.setAttribute('data-voila-jupyter-widget', '');
      view.el.addEventListener('jupyterWidgetResize', (e: Event) => {
        MessageLoop.postMessage(
          view.pWidget,
          LuminoWidget.Widget.ResizeMessage.UnknownSize
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
    // Lazy loading of either ipywidgets 7 or ipywidgets 8 widgets and CSS
    // Depending on what is requested by the kernel, one or the other will load
    this.register({
      name: '@jupyter-widgets/base',
      version: "2.0.0",
      exports: async () => require('@jupyter-widgets/base') as any,
    });
    this.register({
      name: '@jupyter-widgets/controls',
      version: "2.0.0",
      exports: async () => {
        const controlsWidgets = require('@jupyter-widgets/controls') as any;
        require('@jupyter-widgets/controls/css/widgets-base.css');
        return controlsWidgets;
      },
    });
    this.register({
      name: '@jupyter-widgets/output',
      version: "1.0.0",
      exports: async () => (await require('@jupyter-widgets/jupyterlab-manager')).output as any,
    });
    this.register({
      name: '@jupyter-widgets/base',
      version: "1.2.0",
      exports: async () => require('@jupyter-widgets/base7') as any,
    });
    this.register({
      name: '@jupyter-widgets/controls',
      version: "1.5.0",
      exports: async () => {
        const controls7Widget = require('@jupyter-widgets/controls7') as any;
        require('@jupyter-widgets/controls7/css/widgets-base.css');
        return controls7Widget;
      },
    });
  }

  private _loader: (name: any, version: any) => Promise<any>;
}
