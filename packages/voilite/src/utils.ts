import { PageConfig } from '@jupyterlab/coreutils';

// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// Inspired by: https://github.com/jupyterlab/jupyterlab/blob/master/dev_mode/index.js

export function loadScript(url: string) {
  return new Promise((resolve, reject) => {
    const newScript = document.createElement('script');
    newScript.onerror = reject;
    newScript.onload = resolve;
    newScript.async = true;
    document.head.appendChild(newScript);
    newScript.src = url;
  });
}
export async function loadComponent(url: string, scope: string) {
  await loadScript(url);

  // From MIT-licensed https://github.com/module-federation/module-federation-examples/blob/af043acd6be1718ee195b2511adf6011fba4233c/advanced-api/dynamic-remotes/app1/src/App.js#L6-L12
  // eslint-disable-next-line no-undef
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // Initialize the container, it may provide shared modules and may need ours
  // eslint-disable-next-line no-undef
  await container.init(__webpack_share_scopes__.default);
}

export async function createModule(scope: string, module: any) {
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

/**
 * Iterate over active plugins in an extension.
 *
 * #### Notes
 * This also populates the disabled
 */
export function* activePlugins(extension: any, disabledExtensions: string[]) {
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
      disabledExtensions.includes(plugin.id) ||
      disabledExtensions.includes(plugin.id.split(':')[0])
    ) {
      continue;
    }
    yield plugin;
  }
}
