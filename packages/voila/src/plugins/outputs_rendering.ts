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

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { Widget } from '@lumino/widgets';

/**
 * The plugin that renders outputs.
 */
export const renderOutputsPlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:render-outputs',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  activate: (app: JupyterFrontEnd, rendermime: IRenderMimeRegistry): void => {
    // This "app.started.then" is a trick to make sure we render the output only when all plugins are loaded
    // Not using await here because we want this function to return immediately
    // Otherwise it prevents the application to start and resolve the "started" promise...
    app.started.then(() => {
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
      const node = document.getElementById('rendered_cells');
      if (node) {
        const cells = new Widget({ node });
        app.shell.add(cells, 'main');
      }
    });
  }
};
