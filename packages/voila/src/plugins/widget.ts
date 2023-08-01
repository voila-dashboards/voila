/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { PageConfig } from '@jupyterlab/coreutils';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { KernelAPI, ServerConnection } from '@jupyterlab/services';

import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';

import {
  WidgetRenderer,
  KernelWidgetManager
} from '@jupyter-widgets/jupyterlab-manager';

import {
  IJupyterWidgetRegistry,
  IWidgetRegistryData
} from '@jupyter-widgets/base';

import { VoilaApp } from '../app';

import { Widget } from '@lumino/widgets';

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/**
 * The Voila widgets manager plugin.
 */
export const widgetManager: JupyterFrontEndPlugin<IJupyterWidgetRegistry> = {
  id: '@voila-dashboards/voila:widget-manager',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  provides: IJupyterWidgetRegistry,
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<IJupyterWidgetRegistry> => {
    if (!(app instanceof VoilaApp)) {
      throw Error(
        'The Voila Widget Manager plugin must be activated in a VoilaApp'
      );
    }
    const baseUrl = PageConfig.getBaseUrl();
    const kernelId = PageConfig.getOption('kernelId');
    const serverSettings = ServerConnection.makeSettings({ baseUrl });

    const model = await KernelAPI.getKernelModel(kernelId, serverSettings);
    if (!model) {
      return {
        registerWidget(data: IWidgetRegistryData): void {
          throw Error(`The model for kernel id ${kernelId} does not exist`);
        }
      };
    }
    const kernel = new KernelConnection({ model, serverSettings });
    const manager = new KernelWidgetManager(kernel, rendermime);
    app.widgetManager = manager;

    rendermime.removeMimeType(WIDGET_MIMETYPE);
    rendermime.addFactory(
      {
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: (options) => new WidgetRenderer(options, manager)
      },
      -10
    );

    window.addEventListener('beforeunload', (e) => {
      const data = new FormData();
      // it seems if we attach this to early, it will not be called
      const matches = document.cookie.match('\\b_xsrf=([^;]*)\\b');
      const xsrfToken = (matches && matches[1]) || '';
      data.append('_xsrf', xsrfToken);
      window.navigator.sendBeacon(
        `${baseUrl}voila/api/shutdown/${kernel.id}`,
        data
      );
      kernel.dispose();
    });

    return {
      registerWidget: async (data: IWidgetRegistryData) => {
        const manager = await app.widgetManagerPromise.promise;

        manager.register(data);
      }
    };
  }
};

/**
 * The plugin that renders outputs.
 */
export const renderOutputsPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:render-outputs',
  autoStart: true,
  requires: [IRenderMimeRegistry, IJupyterWidgetRegistry],
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<void> => {
    // Render outputs
    const cellOutputs = document.body.querySelectorAll(
      'script[type="application/vnd.voila.cell-output+json"]'
    );

    cellOutputs.forEach(async (cellOutput) => {
      const model = JSON.parse(cellOutput.innerHTML);

      const mimeType = rendermime.preferredMimeType(model.data, 'any');

      if (!mimeType) {
        return null;
      }
      const output = rendermime.createRenderer(mimeType);
      output.renderModel(model).catch((error) => {
        // Manually append error message to output
        const pre = document.createElement('pre');
        pre.textContent = `Javascript Error: ${error.message}`;
        output.node.appendChild(pre);

        // Remove mime-type-specific CSS classes
        pre.className = 'lm-Widget jp-RenderedText';
        pre.setAttribute('data-mime-type', 'application/vnd.jupyter.stderr');
      });

      output.addClass('jp-OutputArea-output');

      if (cellOutput.parentElement) {
        const container = cellOutput.parentElement;

        container.removeChild(cellOutput);

        // Attach output
        Widget.attach(output, container);
      }
    });
  }
};
