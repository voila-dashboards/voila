/***************************************************************************
 * Copyright (c) 2022, Voilà contributors                                   *
 * Copyright (c) 2022, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import * as base from '@jupyter-widgets/base';
import * as controls from '@jupyter-widgets/controls';
import {
  KernelWidgetManager,
  output,
  WidgetRenderer
} from '@jupyter-widgets/jupyterlab-manager';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel } from '@jupyterlab/services';
import { OutputModel } from '@voila-dashboards/voila';

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/**
 * A custom widget manager to render widgets with Voila
 */
export class VoiliteWidgetManager extends KernelWidgetManager {
  constructor(
    kernel: Kernel.IKernelConnection,
    rendermime: IRenderMimeRegistry
  ) {
    super(kernel, rendermime);
    rendermime.addFactory(
      {
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: options => new WidgetRenderer(options, this as any)
      },
      -10
    );
    this._registerWidgets();
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
      exports: {
        ...(output as any),
        OutputModel
      }
    });
  }
}
