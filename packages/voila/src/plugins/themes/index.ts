/***************************************************************************
 * Copyright (c) 2023, Voilà contributors                                   *
 * Copyright (c) 2023, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/
import { StyleModule } from 'style-mod';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IThemeManager } from '@jupyterlab/apputils';
import { jupyterHighlightStyle } from '@jupyterlab/codemirror';
import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { ThemeManager } from './thememanager';

/**
 * The voila theme manager provider.
 */
export const themesManagerPlugin: JupyterFrontEndPlugin<IThemeManager> = {
  id: '@voila-dashboards/voila:theme-manager',
  description: 'Provides the theme manager.',
  requires: [JupyterFrontEnd.IPaths],
  activate: (
    app: JupyterFrontEnd,
    paths: JupyterFrontEnd.IPaths
  ): IThemeManager => {
    const host = app.shell;
    const url = URLExt.join(PageConfig.getBaseUrl(), paths.urls.themes);
    const manager = new ThemeManager({
      host,
      url
    });

    let currentTheme: string;

    manager.themeChanged.connect((sender, args) => {
      // Set data attributes on the application shell for the current theme.
      currentTheme = args.newValue;
      if (currentTheme.length > 0) {
        document.body.dataset.jpThemeLight = String(
          manager.isLight(currentTheme)
        );
        document.body.dataset.jpThemeName = currentTheme;
      }
    });

    return manager;
  },
  autoStart: true,
  provides: IThemeManager
};

/**
 * A plugin to handler the theme
 */
export const themePlugin: JupyterFrontEndPlugin<void> = {
  id: '@voila-dashboards/voila:theme',
  autoStart: true,
  optional: [IThemeManager],
  activate: async (
    app: JupyterFrontEnd,
    themeManager: IThemeManager | null
  ) => {
    if (jupyterHighlightStyle.module) {
      StyleModule.mount(document, jupyterHighlightStyle.module);
    }

    if (!themeManager) {
      return;
    }

    const labThemeName = PageConfig.getOption('jupyterLabTheme');

    // default to the light theme if the theme is not specified (empty)
    const theme = labThemeName || 'light';
    if (theme !== 'dark' && theme !== 'light') {
      await themeManager.setTheme(theme);
    }
    window.themeLoaded = true;
    if (window.cellLoaded) {
      window.voila_finish();
    }
  }
};
