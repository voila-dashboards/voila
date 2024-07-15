/***************************************************************************
 * Copyright (c) 2024, Voilà contributors                                   *
 * Copyright (c) 2024, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import * as base from '@jupyter-widgets/base';
import * as base7 from '@jupyter-widgets/base7';
import { JUPYTER_CONTROLS_VERSION as JUPYTER_CONTROLS7_VERSION } from '@jupyter-widgets/controls7/lib/version';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * The base widgets.
 */
export const baseWidgets7Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:base-${base7.JUPYTER_WIDGETS_VERSION}`,
  requires: [base.IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: base.IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/base',
      version: base7.JUPYTER_WIDGETS_VERSION,
      exports: {
        WidgetModel: base7.WidgetModel as any,
        WidgetView: base7.WidgetView as any,
        DOMWidgetView: base7.DOMWidgetView as any,
        DOMWidgetModel: base7.DOMWidgetModel as any,
        LayoutModel: base7.LayoutModel as any,
        LayoutView: base7.LayoutView as any,
        StyleModel: base7.StyleModel as any,
        StyleView: base7.StyleView as any
      }
    });
  }
};

/**
 * The control widgets.
 */
export const controlWidgets7Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:controls-${JUPYTER_CONTROLS7_VERSION}`,
  requires: [base.IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: base.IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/controls',
      version: JUPYTER_CONTROLS7_VERSION,
      exports: () => {
        return new Promise((resolve, reject) => {
          (require as any).ensure(
            ['@jupyter-widgets/controls7'],
            (require: NodeRequire) => {
              // eslint-disable-next-line @typescript-eslint/no-var-requires
              resolve(require('@jupyter-widgets/controls7'));
            },
            (err: any) => {
              reject(err);
            },
            '@jupyter-widgets/controls7'
          );
        });
      }
    });
  }
};
