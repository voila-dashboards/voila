/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/
import {
  IJupyterWidgetRegistry,
  IWidgetRegistryData
} from '@jupyter-widgets/base';
import { WidgetRenderer } from '@jupyter-widgets/jupyterlab-manager';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { IOutput } from '@jupyterlab/nbformat';
import { OutputAreaModel, SimplifiedOutputArea } from '@jupyterlab/outputarea';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { KernelAPI, ServerConnection } from '@jupyterlab/services';
import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';
import { Widget } from '@lumino/widgets';

import { VoilaApp } from '../../app';
import { VoilaWidgetManager } from './manager';
import { RenderedCells } from './renderedcells';

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
    const manager = new VoilaWidgetManager(kernel, rendermime);
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

    const node = document.getElementById('rendered_cells');
    if (node) {
      const cells = new RenderedCells({ node });
      app.shell.add(cells, 'main');
    }
  }
};

function createOutputArea({
  rendermime,
  parent
}: {
  rendermime: IRenderMimeRegistry;
  parent: Element;
}): OutputAreaModel {
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
  parent.lastElementChild?.appendChild(wrapper);
  area.node.classList.add('jp-Cell-outputArea');

  area.node.style.display = 'flex';
  area.node.style.flexDirection = 'column';

  Widget.attach(area, wrapper);
  return model;
}

/**
 * The plugin that renders outputs.
 */
export const renderOutputsProgressivelyPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:render-outputs-progressively',
  autoStart: true,
  requires: [IRenderMimeRegistry, IJupyterWidgetRegistry],
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<void> => {
    const widgetManager = (app as VoilaApp).widgetManager;
    if (!widgetManager) {
      return;
    }

    const kernelId = (app as VoilaApp).widgetManager?.kernel.id;

    const receivedWidgetModel: {
      [modelId: string]: {
        outputModel: OutputAreaModel;
        executionModel: IOutput;
      };
    } = {};
    const modelRegisteredHandler = (_: VoilaWidgetManager, modelId: string) => {
      if (receivedWidgetModel[modelId]) {
        const { outputModel, executionModel } = receivedWidgetModel[modelId];
        console.log('render later');
        outputModel.add(executionModel);
        widgetManager.removeRegisteredModel(modelId);
      }
    };
    widgetManager.modelRegistered.connect(modelRegisteredHandler);

    const ws = new WebSocket(`ws://localhost:8866/voila/execution/${kernelId}`);

    ws.onmessage = async (msg) => {
      const { action, payload } = JSON.parse(msg.data);
      if (action === 'execution_result') {
        const { cell_index, output_cell } = payload;
        const element = document.querySelector(
          `[cell-index="${cell_index + 1}"]`
        );
        if (element) {
          const skeleton = element
            .getElementsByClassName('voila-skeleton-container')
            .item(0);
          if (skeleton) {
            element.removeChild(skeleton);
          }
          const model = createOutputArea({ rendermime, parent: element });

          if (output_cell.outputs.length > 0) {
            element.lastElementChild?.classList.remove(
              'jp-mod-noOutputs',
              'jp-mod-noInput'
            );
          }
          for (const outputData of output_cell.outputs) {
            const modelId =
              outputData?.data?.['application/vnd.jupyter.widget-view+json']
                ?.model_id;
            if (modelId) {
              if (widgetManager.has_model(modelId)) {
                console.log('render immediatly');
                model.add(outputData);
              } else {
                receivedWidgetModel[modelId] = {
                  outputModel: model,
                  executionModel: outputData
                };
              }
            } else {
              model.add(outputData);
            }
          }
        }
      } else if (action === 'finished') {
        widgetManager.modelRegistered.disconnect(modelRegisteredHandler);
        ws.close();
      }
    };
    ws.onopen = () => {
      ws.send(
        JSON.stringify({ action: 'execute', payload: { kernel_id: kernelId } })
      );
    };
  }
};

export { VoilaWidgetManager };
