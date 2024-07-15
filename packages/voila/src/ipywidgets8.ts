/***************************************************************************
 * Copyright (c) 2024, Voilà contributors                                   *
 * Copyright (c) 2024, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import * as base from '@jupyter-widgets/base';
import { JUPYTER_CONTROLS_VERSION } from '@jupyter-widgets/controls/lib/version';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * The base widgets.
 */
export const baseWidgets8Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:base-${base.JUPYTER_WIDGETS_VERSION}`,
  requires: [base.IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: base.IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/base',
      version: base.JUPYTER_WIDGETS_VERSION,
      exports: {
        WidgetModel: base.WidgetModel as any,
        WidgetView: base.WidgetView as any,
        DOMWidgetView: base.DOMWidgetView as any,
        DOMWidgetModel: base.DOMWidgetModel as any,
        LayoutModel: base.LayoutModel as any,
        LayoutView: base.LayoutView as any,
        StyleModel: base.StyleModel as any,
        StyleView: base.StyleView as any
      }
    });
  }
};

/**
 * The control widgets.
 */
export const controlWidgets8Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:controls-${JUPYTER_CONTROLS_VERSION}`,
  requires: [base.IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: base.IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/controls',
      version: JUPYTER_CONTROLS_VERSION,
      exports: () => {
        return new Promise((resolve, reject) => {
          (require as any).ensure(
            ['@jupyter-widgets/controls'],
            (require: NodeRequire) => {
              // eslint-disable-next-line @typescript-eslint/no-var-requires
              resolve(require('@jupyter-widgets/controls'));
            },
            (err: any) => {
              reject(err);
            },
            '@jupyter-widgets/controls'
          );
        });
      }
    });
  }
};
