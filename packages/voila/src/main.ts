/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 * Copyright (c) Jupyter Development Team.                                  *
 * Distributed under the terms of the Modified BSD License.                 *
 ****************************************************************************/
import './sharedscope';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

import { VoilaApp } from './app';
import plugins from './voilaplugins';
import { baseWidgets7Plugin, controlWidgets7Plugin } from './ipywidgets7';
import { baseWidgets8Plugin, controlWidgets8Plugin } from './ipywidgets8';
import { VoilaServiceManager } from './services/servicemanager';
import { VoilaShell } from './shell';
import {
  IFederatedExtensionData,
  activePlugins,
  createModule,
  loadComponent,
  shouldUseMathJax2
} from './tools';

//Inspired by: https://github.com/jupyterlab/jupyterlab/blob/master/dev_mode/index.js

/**
 * The main function
 */
async function main() {
  const mods = [
    // @jupyterlab plugins
    require('@jupyterlab/codemirror-extension').default.filter(
      (p: any) => p.id === '@jupyterlab/codemirror-extension:languages'
    ),
    require('@jupyterlab/markedparser-extension'),
    require('@jupyterlab/rendermime-extension'),
    require('@jupyterlab/theme-light-extension'),
    require('@jupyterlab/theme-dark-extension'),
    require('@jupyter-widgets/jupyterlab-manager/lib/plugin').default.filter(
      (p: any) => p.id !== '@jupyter-widgets/jupyterlab-manager:plugin'
    ),
    plugins,
    // For backward compat with ipywidgets 7
    baseWidgets7Plugin,
    controlWidgets7Plugin,
    // For compat with ipywidgets 8
    baseWidgets8Plugin,
    controlWidgets8Plugin
  ];

  if (shouldUseMathJax2()) {
    mods.push(require('@jupyterlab/mathjax2-extension'));
  } else {
    mods.push(require('@jupyterlab/mathjax-extension'));
  }

  const mimeExtensions = [
    require('@jupyterlab/javascript-extension'),
    require('@jupyterlab/json-extension'),
    require('@jupyterlab/vega5-extension')
  ];
  const extensionData: IFederatedExtensionData[] = JSON.parse(
    PageConfig.getOption('federated_extensions')
  );
  const federatedExtensionPromises: Promise<any>[] = [];
  const federatedMimeExtensionPromises: Promise<any>[] = [];
  const federatedStylePromises: Promise<any>[] = [];

  const extensions = await Promise.allSettled(
    extensionData.map(async (data) => {
      await loadComponent(
        `${URLExt.join(
          PageConfig.getOption('fullLabextensionsUrl'),
          data.name,
          data.load
        )}`,
        data.name
      );
      return data;
    })
  );

  extensions.forEach((p) => {
    if (p.status === 'rejected') {
      // There was an error loading the component
      console.error(p.reason);
      return;
    }

    const data = p.value;

    if (data.extension) {
      federatedExtensionPromises.push(createModule(data.name, data.extension));
    }
    if (data.mimeExtension) {
      federatedMimeExtensionPromises.push(
        createModule(data.name, data.mimeExtension)
      );
    }
    if (data.style) {
      federatedStylePromises.push(createModule(data.name, data.style));
    }
  });

  // Add the federated extensions.
  const federatedExtensions = await Promise.allSettled(
    federatedExtensionPromises
  );
  federatedExtensions.forEach((p) => {
    if (p.status === 'fulfilled') {
      for (const plugin of activePlugins(p.value, [])) {
        mods.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  // Add the federated mime extensions.
  const federatedMimeExtensions = await Promise.allSettled(
    federatedMimeExtensionPromises
  );
  federatedMimeExtensions.forEach((p) => {
    if (p.status === 'fulfilled') {
      for (const plugin of activePlugins(p.value, [])) {
        mimeExtensions.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  // Load all federated component styles and log errors for any that do not
  (await Promise.allSettled(federatedStylePromises))
    .filter(({ status }) => status === 'rejected')
    .forEach((p) => {
      console.error((p as PromiseRejectedResult).reason);
    });

  const app = new VoilaApp({
    mimeExtensions,
    shell: new VoilaShell(),
    serviceManager: new VoilaServiceManager()
  });
  app.registerPluginModules(mods);
  await app.start();
  window.jupyterapp = app;
}

window.addEventListener('load', main);
