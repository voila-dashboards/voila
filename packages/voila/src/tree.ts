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

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

import { VoilaApp } from './app';
import {
  pathsPlugin,
  themePlugin,
  themesManagerPlugin,
  translatorPlugin
} from './voilaplugins';
import { VoilaServiceManager } from './services/servicemanager';
import { VoilaShell } from './shell';
import { activePlugins, createModule, loadComponent } from './tools';
import '../style/index.js';
import '@jupyterlab/filebrowser/style/index.js';
import { treeWidgetPlugin } from './plugins/tree';
import { Drive } from '@jupyterlab/services';
import { ContentsManager } from '@jupyterlab/services';

const disabled = [
  '@jupyter-widgets/jupyterlab-manager:plugin',
  '@jupyter-widgets/jupyterlab-manager:saveWidgetState',
  '@jupyter-widgets/jupyterlab-manager:base-2.0.0',
  '@jupyter-widgets/jupyterlab-manager:controls-2.0.0',
  '@jupyter-widgets/jupyterlab-manager:output-1.0.0'
];

/**
 * The main function
 */
async function main() {
  const mods = [
    require('@jupyterlab/theme-light-extension'),
    require('@jupyterlab/theme-dark-extension'),
    pathsPlugin,
    translatorPlugin,
    themePlugin,
    themesManagerPlugin,
    treeWidgetPlugin
  ];

  const mimeExtensions: any[] = [];

  const extensionData: any[] = JSON.parse(
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
      for (const plugin of activePlugins(p.value, disabled)) {
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
      for (const plugin of activePlugins(p.value, disabled)) {
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
  const drive = new Drive({ apiEndpoint: 'voila/api/contents' });
  const cm = new ContentsManager({ defaultDrive: drive });
  const app = new VoilaApp({
    mimeExtensions,
    shell: new VoilaShell(),
    serviceManager: new VoilaServiceManager({ contents: cm })
  });
  app.registerPluginModules(mods);
  app.started.then(() => {
    const el = document.getElementById('voila-tree-main');
    if (el) {
      el.style.display = 'unset';
    }
  });
  await app.start();
}
window.addEventListener('load', main);
