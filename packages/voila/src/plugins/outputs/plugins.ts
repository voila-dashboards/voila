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
import { Widget } from '@lumino/widgets';

import { VoilaApp } from '../../app';
import { RenderedCells } from './renderedcells';
import {
  createSkeleton,
  getExecutionURL,
  handleExecutionResult,
  IExecutionMessage,
  IReceivedWidgetModel
} from './tools';

/**
 * The plugin that renders outputs.
 */
export const renderOutputsPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:render-outputs',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<void> => {
    app.started.then(() => {
      // TODO: Typeset a fake element to get MathJax loaded, remove this hack once
      // MathJax 2 is removed.
      rendermime.latexTypesetter?.typeset(document.createElement('div'));

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
    });
  }
};

/**
 * The plugin that renders outputs.
 */
export const renderOutputsProgressivelyPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:render-outputs-progressively',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<void> => {
    const progressiveRendering =
      PageConfig.getOption('progressiveRendering') === 'true';
    if (!progressiveRendering) {
      return;
    }

    createSkeleton();

    const widgetManager = await (app as VoilaApp).widgetManagerPromise.promise;

    if (!widgetManager) {
      return;
    }

    const kernelId = widgetManager.kernel.id;

    const receivedWidgetModel: IReceivedWidgetModel = {};
    const modelRegisteredHandler = (_: any, modelId: string) => {
      if (receivedWidgetModel[modelId]) {
        const { outputModel, executionModel } = receivedWidgetModel[modelId];
        outputModel.add(executionModel);
        widgetManager.removeRegisteredModel(modelId);
      }
    };
    widgetManager.modelRegistered.connect(modelRegisteredHandler);
    const wsUrl = getExecutionURL(kernelId);
    const ws = new WebSocket(wsUrl);
    ws.onmessage = async (msg) => {
      const { action, payload }: IExecutionMessage = JSON.parse(msg.data);
      switch (action) {
        case 'execution_result': {
          const result = handleExecutionResult({
            payload,
            rendermime,
            widgetManager
          });
          if (result) {
            Object.entries(result).forEach(([key, val]) => {
              receivedWidgetModel[key] = val;
            });
          }
          const { cell_index, total_cell } = payload;
          if (cell_index + 1 === total_cell) {
            // Executed all cells
            ws.close();
          }

          break;
        }
        case 'execution_error': {
          console.error(`Execution error: ${payload.error}`);
          break;
        }
        default:
          break;
      }
    };
    ws.onopen = () => {
      ws.send(
        JSON.stringify({ action: 'execute', payload: { kernel_id: kernelId } })
      );
    };
  }
};
