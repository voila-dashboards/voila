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
import { WidgetRenderer, output } from '@jupyter-widgets/jupyterlab-manager';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PageConfig } from '@jupyterlab/coreutils';
import { IRenderMime, IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { KernelAPI, ServerConnection } from '@jupyterlab/services';
import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';

import { VoilaWidgetManager } from './manager';

const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

class VoilaWidgetRenderer extends WidgetRenderer {
  constructor(
    options: IRenderMime.IRendererOptions,
    manager: VoilaWidgetManager
  ) {
    super(options, manager);

    this.voilaManager = manager;
  }

  async renderModel(model: IRenderMime.IMimeModel): Promise<void> {
    await this.voilaManager.loadedModelsFromKernel;

    return super.renderModel(model);
  }

  private voilaManager: VoilaWidgetManager;
}

/**
 * The Voila widgets manager plugin.
 */
const widgetManager: JupyterFrontEndPlugin<IJupyterWidgetRegistry> = {
  id: '@voila-dashboards/voila:widget-manager7',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  provides: IJupyterWidgetRegistry,
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<IJupyterWidgetRegistry> => {
    if (app.name !== 'Voila') {
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
            // eslint-disable-next-line @typescript-eslint/no-empty-function
            connect: () => {}
          }
        },
        statusChanged: {
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          connect: () => {}
        },
        kernelChanged: {
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          connect: () => {}
        },
        connectionStatusChanged: {
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          connect: () => {}
        }
      },
      saveState: {
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        connect: () => {}
      }
    };

    const settings = {
      saveState: false
    };

    const manager = new VoilaWidgetManager(
      context as any,
      rendermime,
      settings
    );
    (app as any).widgetManager = manager;

    rendermime.removeMimeType(WIDGET_MIMETYPE);
    rendermime.addFactory(
      {
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: (options) => new VoilaWidgetRenderer(options, manager)
      },
      -10
    );

    manager.register({
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

    manager.register({
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

    manager.register({
      name: '@jupyter-widgets/output',
      version: output.OUTPUT_WIDGET_VERSION,
      exports: output as any
    });

    app.started.then(async () => {
      await manager._loadFromKernel();
    });

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

export default [widgetManager];
