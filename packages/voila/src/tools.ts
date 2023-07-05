import { PageConfig } from '@jupyterlab/coreutils';

export function loadScript(url: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const newScript = document.createElement('script');
    newScript.onerror = reject;
    newScript.onload = resolve;
    newScript.async = true;
    document.head.appendChild(newScript);
    newScript.src = url;
  });
}

export async function loadComponent(url: string, scope: string): Promise<void> {
  await loadScript(url);

  // From MIT-licensed https://github.com/module-federation/module-federation-examples/blob/af043acd6be1718ee195b2511adf6011fba4233c/advanced-api/dynamic-remotes/app1/src/App.js#L6-L12
  // eslint-disable-next-line no-undef
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // Initialize the container, it may provide shared modules and may need ours
  // eslint-disable-next-line no-undef
  await container.init(__webpack_share_scopes__.default);
}

export async function createModule(
  scope: string,
  module: string
): Promise<any> {
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
export function* activePlugins(
  extension: any,
  disabledExtensions: string[]
): Generator<any> {
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

export interface IFederatedExtensionData {
  name: string;
  load: string;
  extension?: string;
  style?: string;
  mimeExtension?: string;
}
/**
 * Create a list of extension to be loaded from the
 * available extensions and the black/white list
 * configuration
 *
 * @export
 * @param {IFederatedExtensionData[]} pageConfigData
 * @param {string[]} blackList
 * @param {string[]} whileList
 * @return {*}  {IFederatedExtensionData[]}
 */
export function resolveFederatedExtension(options: {
  pageConfigExtensionData: IFederatedExtensionData[];
  blackList: string[];
  whiteList: string[];
}): IFederatedExtensionData[] {
  const mustHave = ['@jupyter-widgets/jupyterlab-manager'];
  const { pageConfigExtensionData, blackList, whiteList } = options;
  if (blackList.length === 0) {
    if (whiteList.length === 0) {
      // No white and black list, return all
      return pageConfigExtensionData;
    }
    /// White list is not empty, return white listed only
    return pageConfigExtensionData.filter(
      (item) => mustHave.includes(item.name) || whiteList.includes(item.name)
    );
  }
  if (whiteList.length === 0) {
    // No white list, return non black listed only
    return pageConfigExtensionData.filter(
      (item) => mustHave.includes(item.name) || !blackList.includes(item.name)
    );
  }
  /// Have both black and white list, use only white list
  return pageConfigExtensionData.filter(
    (item) => mustHave.includes(item.name) || whiteList.includes(item.name)
  );
}
