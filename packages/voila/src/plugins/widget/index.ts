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

import { VoilaApp } from '../../app';

import { Widget } from '@lumino/widgets';
import { RenderedCells } from './renderedcells';
import {
  // OutputArea,
  OutputAreaModel,
  SimplifiedOutputArea
} from '@jupyterlab/outputarea';

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
    // TODO: Typeset a fake element to get MathJax loaded, remove this hack once
    // MathJax 2 is removed.
    await rendermime.latexTypesetter?.typeset(document.createElement('div'));

    // Render latex in markdown cells
    const mdOutput = document.body.querySelectorAll('div.jp-MarkdownOutput');
    mdOutput.forEach((md) => {
      rendermime.latexTypesetter?.typeset(md as HTMLElement);
    });
    // Render code cell
    // const cellOutputs = document.body.querySelectorAll(
    //   'script[type="application/vnd.voila.cell-output+json"]'
    // );
    // cellOutputs.forEach(async (cellOutput) => {
    //   const model = JSON.parse(cellOutput.innerHTML);

    //   const mimeType = rendermime.preferredMimeType(model.data, 'any');

    //   if (!mimeType) {
    //     return null;
    //   }
    //   const output = rendermime.createRenderer(mimeType);
    //   output.renderModel(model).catch((error) => {
    //     // Manually append error message to output
    //     const pre = document.createElement('pre');
    //     pre.textContent = `Javascript Error: ${error.message}`;
    //     output.node.appendChild(pre);

    //     // Remove mime-type-specific CSS classes
    //     pre.className = 'lm-Widget jp-RenderedText';
    //     pre.setAttribute('data-mime-type', 'application/vnd.jupyter.stderr');
    //   });

    //   output.addClass('jp-OutputArea-output');

    //   if (cellOutput.parentElement) {
    //     const container = cellOutput.parentElement;

    //     container.removeChild(cellOutput);

    //     // Attach output
    //     Widget.attach(output, container);
    //   }
    // });
    const kernelId = (app as VoilaApp).widgetManager?.kernel.id;
    console.log('using kernel', kernelId);
    const ws = new WebSocket(`ws://localhost:8866/voila/execution/${kernelId}`);
    ws.onmessage = (msg) => {
      const { action, payload } = JSON.parse(msg.data);
      if (action === 'execution_result') {
        const { cell_index, output_cell, request_kernel_id } = payload;
        const element = document.querySelector(
          `[cell-index="${cell_index + 1}"]`
        );
        if (element) {
          const model = new OutputAreaModel({ trusted: true });
          const area = new SimplifiedOutputArea({
            model,
            rendermime
          });

          const wrapper = document.createElement('div');
          wrapper.classList.add('jp-Cell-outputWrapper');
          const collapser = document.createElement('div');
          collapser.classList.add(
            'jp-Collapser',
            'jp-OutputCollapser',
            'jp-Cell-outputCollapser'
          );
          wrapper.appendChild(collapser);
          element.lastElementChild?.appendChild(wrapper);

          area.node.classList.add('jp-Cell-outputArea');

          // Why do we need this? Are we missing a CSS class?
          area.node.style.display = 'flex';
          area.node.style.flexDirection = 'column';

          Widget.attach(area, wrapper);
          const skeleton = element
            .getElementsByClassName('voila-skeleton-container')
            .item(0);
          if (skeleton) {
            element.removeChild(skeleton);
          }
          const outputData = output_cell.outputs[0];
          if (outputData) {
            console.log(
              'adding',
              outputData,
              'request_kernel_id',
              request_kernel_id,
              'kernelId',
              kernelId
            );
            element.lastElementChild?.classList.remove(
              'jp-mod-noOutputs',
              'jp-mod-noInput'
            );
            model.add(outputData);
          }
        }
      }
    };
    ws.onopen = () => {
      console.log('opened');
      ws.send(
        JSON.stringify({ action: 'execute', payload: { kernel_id: kernelId } })
      );
    };

    const node = document.getElementById('rendered_cells');
    if (node) {
      const cells = new RenderedCells({ node });
      app.shell.add(cells, 'main');
    }
  }
};
