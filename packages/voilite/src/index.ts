/***************************************************************************
 * Copyright (c) 2022, Voilà contributors                                   *
 * Copyright (c) 2022, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/
import '@jupyterlab/nbconvert-css/style/index.css';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { JupyterLiteServer } from '@jupyterlite/server';
import { VoilaShell } from '@voila-dashboards/voila';

import { VoiliteApp } from './app';
import plugins from './plugins';

// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// Inspired by: https://github.com/jupyterlab/jupyterlab/blob/master/dev_mode/index.js

function loadScript(url: string) {
  return new Promise((resolve, reject) => {
    const newScript = document.createElement('script');
    newScript.onerror = reject;
    newScript.onload = resolve;
    newScript.async = true;
    document.head.appendChild(newScript);
    newScript.src = url;
  });
}
async function loadComponent(url: string, scope: string) {
  await loadScript(url);

  // From MIT-licensed https://github.com/module-federation/module-federation-examples/blob/af043acd6be1718ee195b2511adf6011fba4233c/advanced-api/dynamic-remotes/app1/src/App.js#L6-L12
  // eslint-disable-next-line no-undef
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // Initialize the container, it may provide shared modules and may need ours
  // eslint-disable-next-line no-undef
  await container.init(__webpack_share_scopes__.default);
}

async function createModule(scope: string, module: any) {
  try {
    const factory = await window._JUPYTERLAB[scope].get(module);
    return factory();
  } catch (e) {
    console.warn(
      `Failed to create module: package: ${scope}; module: ${module}`
    );
    throw e;
  }
}

const serverExtensions = [
  // import('@jupyterlite/javascript-kernel-extension'),
  import('@jupyterlite/pyolite-kernel-extension'),
  import('@jupyterlite/server-extension')
];

const disabled = ['@jupyter-widgets/jupyterlab-manager'];

/**
 * The main function
 */
async function main() {
  const mods = [
    // @jupyterlab plugins
    require('@jupyterlab/apputils-extension').default.filter((m: any) =>
      [
        '@jupyterlab/apputils-extension:settings',
        '@jupyterlab/apputils-extension:themes'
      ].includes(m.id)
    ),
    require('@jupyterlab/markdownviewer-extension'),
    require('@jupyterlab/mathjax2-extension'),
    require('@jupyterlab/rendermime-extension'),
    // TODO: add the settings endpoint to re-enable the theme plugins?
    // This would also need the theme manager plugin and settings
    require('@jupyterlab/theme-light-extension'),
    require('@jupyterlab/theme-dark-extension'),
    plugins
  ];

  const mimeExtensions = [
    require('@jupyterlite/iframe-extension'),
    require('@jupyterlab/json-extension')
  ];

  /**
   * Iterate over active plugins in an extension.
   *
   * #### Notes
   * This also populates the disabled
   */
  function* activePlugins(extension: any) {
    // Handle commonjs or es2015 modules
    let exports;
    if (Object.prototype.hasOwnProperty.call(extension, '__esModule')) {
      exports = extension.default;
    } else {
      // CommonJS exports.
      exports = extension;
    }

    const plugins = Array.isArray(exports) ? exports : [exports];
    for (const plugin of plugins) {
      if (
        PageConfig.Extension.isDisabled(plugin.id) ||
        disabled.includes(plugin.id) ||
        disabled.includes(plugin.id.split(':')[0])
      ) {
        continue;
      }
      yield plugin;
    }
  }

  const extensionData = JSON.parse(
    PageConfig.getOption('federated_extensions')
  );

  const federatedExtensionPromises: any[] = [];
  const federatedMimeExtensionPromises: any[] = [];
  const federatedStylePromises: any[] = [];

  const extensions = await Promise.allSettled(
    extensionData.map(async (data: any) => {
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

  Object.entries(extensions).forEach(([_, p]) => {
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
  federatedExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (const plugin of activePlugins(p.value)) {
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
  federatedMimeExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (const plugin of activePlugins(p.value)) {
        mimeExtensions.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  // Load all federated component styles and log errors for any that do not
  (await Promise.allSettled(federatedStylePromises))
    .filter(({ status }) => status === 'rejected')
    .forEach(p => {
      console.error((p as PromiseRejectedResult).reason);
    });

  const litePluginsToRegister: any[] = [];
  const baseServerExtensions = await Promise.all(serverExtensions);
  baseServerExtensions.forEach(p => {
    for (const plugin of activePlugins(p)) {
      litePluginsToRegister.push(plugin);
    }
  });
  console.log('start server');

  // create the in-browser JupyterLite Server
  const jupyterLiteServer = new JupyterLiteServer({ shell: null as never });

  jupyterLiteServer.registerPluginModules(litePluginsToRegister);
  // start the server
  await jupyterLiteServer.start();
  console.log('done  server');
  const serviceManager = jupyterLiteServer.serviceManager;
  const app = new VoiliteApp({
    serviceManager: serviceManager as any,
    mimeExtensions,
    shell: new VoilaShell()
  });

  app.registerPluginModules(mods);

  await app.start();
  await app.renderWidgets();
  window.jupyterapp = app;
}

window.addEventListener('load', main);
