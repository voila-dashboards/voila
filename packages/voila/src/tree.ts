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
import '../style/index.js';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { ContentsManager, Drive } from '@jupyterlab/services';

import { VoilaApp } from './app';
import { treeWidgetPlugin } from './plugins/tree';
import { VoilaServiceManager } from './services/servicemanager';
import { VoilaShell } from './shell';
import { activePlugins, createModule, loadComponent } from './tools';
import {
  pathsPlugin,
  themePlugin,
  themesManagerPlugin,
  translatorPlugin
} from './voilaplugins';

/**
 * The main function
 */
async function main() {
  const mods = [
    require('@jupyterlab/theme-light-extension'),
    require('@jupyterlab/theme-dark-extension'),
    require('@jupyterlab/rendermime-extension'),
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
