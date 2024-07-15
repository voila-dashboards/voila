/***************************************************************************
 * Copyright (c) 2024, Voilà contributors                                   *
 * Copyright (c) 2024, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

import * as base from '@jupyter-widgets/base';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

const JUPYTER_WIDGETS_VERSION = '1.2.0';
const JUPYTER_CONTROLS_VERSION = '1.5.0';

/**
 * The base widgets.
 */
export const baseWidgets7Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:base-${JUPYTER_WIDGETS_VERSION}`,
  requires: [base.IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: base.IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/base',
      version: JUPYTER_WIDGETS_VERSION,
      exports: () => {
        return require('@jupyter-widgets/base7') as any;
      }
    });
  }
};

/**
 * The control widgets.
 */
export const controlWidgets7Plugin: JupyterFrontEndPlugin<void> = {
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
        const controlsWidgets = require('@jupyter-widgets/controls7') as any;
        require('@jupyter-widgets/controls7/css/widgets-base.css');
        return controlsWidgets;
      }
    });
  }
};
