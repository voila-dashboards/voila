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

import { KernelAPI, ServerConnection } from '@jupyterlab/services';

import { KernelConnection } from '@jupyterlab/services/lib/kernel/default';

import { ITranslator, TranslationManager } from '@jupyterlab/translation';

import {
  IJupyterWidgetRegistry,
  IWidgetRegistryData
} from '@jupyter-widgets/base';

import { VoilaApp } from './app';

import { WidgetManager as VoilaWidgetManager } from './manager';

/**
 * The default paths.
 */
const paths: JupyterFrontEndPlugin<JupyterFrontEnd.IPaths> = {
  id: '@voila-dashboards/voila:paths',
  activate: (
    app: JupyterFrontEnd<JupyterFrontEnd.IShell>
  ): JupyterFrontEnd.IPaths => {
    return (app as VoilaApp).paths;
  },
  autoStart: true,
  provides: JupyterFrontEnd.IPaths
};

/**
 * A plugin to stop polling the kernels, sessions and kernel specs.
 *
 * TODO: a cleaner solution would involve a custom ServiceManager to the VoilaApp
 * to prevent the default behavior of polling the /api endpoints.
 */
const stopPolling: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:stop-polling',
  autoStart: true,
  activate: (app: JupyterFrontEnd): void => {
    app.serviceManager.sessions?.ready.then(value => {
      app.serviceManager.sessions['_kernelManager']['_pollModels']?.stop();
      void app.serviceManager.sessions['_pollModels'].stop();
    });

    app.serviceManager.kernelspecs?.ready.then(value => {
      void app.serviceManager.kernelspecs.dispose();
    });
  }
};

/**
 * A simplified Translator
 */
const translator: JupyterFrontEndPlugin<ITranslator> = {
  id: '@voila-dashboards/voila:translator',
  activate: (app: JupyterFrontEnd<JupyterFrontEnd.IShell>): ITranslator => {
    const translationManager = new TranslationManager();
    return translationManager;
  },
  autoStart: true,
  provides: ITranslator
};

/**
 * The Voila widgets manager plugin.
 */
const widgetManager: JupyterFrontEndPlugin<IJupyterWidgetRegistry> = {
  id: '@voila-dashboards/voila:widget-manager',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  provides: IJupyterWidgetRegistry,
  activate: async (
    app: JupyterFrontEnd,
    rendermime: IRenderMimeRegistry
  ): Promise<IJupyterWidgetRegistry> => {
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

    manager.restored.connect(() => {
      void manager.build_widgets();
    });

    window.addEventListener('beforeunload', e => {
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

    console.log('Voila manager activated');

    return {
      registerWidget(data: IWidgetRegistryData): void {
        manager.register(data);
      }
    };
  }
};

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
  paths,
  stopPolling,
  translator,
  widgetManager
];

export default plugins;
