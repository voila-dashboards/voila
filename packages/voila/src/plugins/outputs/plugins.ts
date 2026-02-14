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
import { createOutputArea, createSkeleton, executeCode } from './tools';

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

    const cells = document.querySelectorAll('[cell-index]');
    const cellsNumber = cells.length;
    for (let cellIdx = 0; cellIdx < cellsNumber; cellIdx++) {
      const el = cells.item(cellIdx);
      const codeCell =
        el.getElementsByClassName('jp-CodeCell').item(0) ||
        el.getElementsByClassName('code_cell').item(0); // for classic template;
      if (codeCell) {
        const { area } = createOutputArea({ rendermime, parent: codeCell });
        const source = `${cellIdx}`;
        executeCode(source, area, widgetManager.kernel).then((future) => {
          const skeleton = el
            .getElementsByClassName('voila-skeleton-container')
            .item(0);
          if (skeleton) {
            el.removeChild(skeleton);
          }
        });
      }
    }
  }
};
