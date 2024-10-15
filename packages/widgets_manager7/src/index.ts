/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/
import {
  JUPYTER_WIDGETS_VERSION,
  IJupyterWidgetRegistry,
  IWidgetRegistryData,
  WidgetModel,
  WidgetView,
  DOMWidgetModel,
  DOMWidgetView,
  LayoutModel,
  LayoutView,
  StyleModel,
  StyleView
} from '@jupyter-widgets/base';
import { JUPYTER_CONTROLS_VERSION } from '@jupyter-widgets/controls/lib/version';
import { WidgetRenderer } from '@jupyter-widgets/jupyterlab-manager';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { KernelAPI, ServerConnection } from '@jupyterlab/services';
import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';

import { VoilaWidgetManager } from './manager';


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
    if (app.name !== 'Voila'){
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

    const context = {
      sessionContext: {
          session: {
              kernel,
              kernelChanged: {
                  connect: () => {}
              },
          },
          statusChanged: {
              connect: () => {}
          },
          kernelChanged: {
              connect: () => {}
          },
          connectionStatusChanged: {
              connect: () => {}
          },
      },
      saveState: {
          connect: () => {}
      },
    };

    const settings = {
      saveState: false
    };

    const manager = new VoilaWidgetManager(context as any, rendermime, settings);
    (app as any).widgetManager = manager;

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
        const manager = await (app as any).widgetManagerPromise.promise;

        manager.register(data);
      }
    };
  }
};

/**
 * The base widgets.
 */
export const baseWidgets7Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:base-${JUPYTER_WIDGETS_VERSION}`,
  requires: [IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: IJupyterWidgetRegistry
  ): void => {
    registry.registerWidget({
      name: '@jupyter-widgets/base',
      version: JUPYTER_WIDGETS_VERSION,
      exports: {
        WidgetModel: WidgetModel as any,
        WidgetView: WidgetView as any,
        DOMWidgetView: DOMWidgetView as any,
        DOMWidgetModel: DOMWidgetModel as any,
        LayoutModel: LayoutModel as any,
        LayoutView: LayoutView as any,
        StyleModel: StyleModel as any,
        StyleView: StyleView as any
      }
    });
  }
};

/**
 * The control widgets.
 */
export const controlWidgets7Plugin: JupyterFrontEndPlugin<void> = {
  id: `@jupyter-widgets/jupyterlab-manager:controls-${JUPYTER_CONTROLS_VERSION}`,
  requires: [IJupyterWidgetRegistry],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    registry: IJupyterWidgetRegistry
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
