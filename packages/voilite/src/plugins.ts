import { PageConfig } from '@jupyterlab/coreutils';
/***************************************************************************
 * Copyright (c) 2022, Voilà contributors                                   *
 * Copyright (c) 2022, QuantStack                                           *
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
import { IThemeManager } from '@jupyterlab/apputils';
import { ITranslator, TranslationManager } from '@jupyterlab/translation';
import { PromiseDelegate } from '@lumino/coreutils';
import { VoilaApp } from '@voila-dashboards/voila';

import { VoiliteWidgetManager } from './manager';

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

export const managerPromise = new PromiseDelegate<VoiliteWidgetManager>();

/**
 * The Voila widgets manager plugin.
 */
const widgetManager = {
  id: '@voila-dashboards/voilite:widget-manager',
  autoStart: true,
  provides: base.IJupyterWidgetRegistry,
  activate: async (): Promise<any> => {
    return {
      registerWidget: async (data: any) => {
        const manager = await managerPromise.promise;
        manager.register(data);
      }
    };
  }
};

/**
 * A plugin to handler the theme
 */
const themePlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voilite:theme-manager',
  autoStart: true,
  optional: [IThemeManager],
  activate: (app: JupyterFrontEnd, themeManager: IThemeManager | null) => {
    if (!themeManager) {
      return;
    }
    const labThemeName = PageConfig.getOption('labThemeName');

    const search = window.location.search;
    const urlParams = new URLSearchParams(search);
    const theme = urlParams.get('theme')?.trim() ?? labThemeName;

    const themeName = decodeURIComponent(theme);

    themeManager.setTheme(themeName);
  }
};

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
  paths,
  stopPolling,
  translator,
  widgetManager,
  themePlugin
];

export default plugins;
