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
import { PromiseDelegate } from '@lumino/coreutils';
import { translatorPlugin, pathsPlugin } from '@voila-dashboards/voila';
import { PageConfig } from '@jupyterlab/coreutils';
import { VoiliteWidgetManager } from './manager';

export const managerPromise = new PromiseDelegate<VoiliteWidgetManager>();

/**
 * The Voilite widgets manager plugin.
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
  pathsPlugin,
  translatorPlugin,
  widgetManager,
  themePlugin
];

export default plugins;
