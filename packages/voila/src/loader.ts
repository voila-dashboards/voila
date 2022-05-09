/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/

const cdn = 'https://cdn.jsdelivr.net/npm/';

/**
 * Load a package using requirejs and return a promise
 *
 * @param pkg Package name or names to load
 */
function requirePromise(pkg: string[]) {
  return new Promise((resolve, reject) => {
    const require = window.requirejs;
    if (require === undefined) {
      reject('Requirejs is needed, please ensure it is loaded on the page.');
    } else {
      require(pkg, resolve, reject);
    }
  });
}

function moduleNameToCDNUrl(moduleName: string, moduleVersion: string) {
  let packageName = moduleName;
  let fileName = 'index'; // default filename
  // if a '/' is present, like 'foo/bar', packageName is changed to 'foo', and path to 'bar'
  // We first find the first '/'
  let index = moduleName.indexOf('/');
  if (index !== -1 && moduleName[0] === '@') {
    // if we have a namespace, it's a different story
    // @foo/bar/baz should translate to @foo/bar and baz
    // so we find the 2nd '/'
    index = moduleName.indexOf('/', index + 1);
  }
  if (index !== -1) {
    fileName = moduleName.substr(index + 1);
    packageName = moduleName.substr(0, index);
  }

  if (moduleVersion.startsWith('~')) {
    moduleVersion = moduleVersion.slice(1);
  }

  return {
    packageRoot: `${cdn}${packageName}@${moduleVersion}`,
    pathGuess: `/dist/${fileName}`
  };
}

/**
 * Load an amd module locally and fall back to specified CDN if unavailable.
 *
 * @param moduleName The name of the module to load..
 * @param version The semver range for the module, if loaded from a CDN.
 *
 * By default, the CDN service used is cdn.jsdelivr.net. However, this default can be
 * overridden by specifying another URL via the HTML attribute
 * "data-jupyter-widgets-cdn" on a script tag of the page.
 *
 * The semver range is only used with the CDN.
 */
export function requireLoader(
  moduleName: string,
  moduleVersion: string
): Promise<any> {
  return requirePromise([`${moduleName}`]).catch(err => {
    const failedId = err.requireModules && err.requireModules[0];
    if (failedId) {
      console.log(`Falling back to ${cdn} for ${moduleName}@${moduleVersion}`);
      const require = window.requirejs;
      if (require === undefined) {
        throw new Error(
          'Requirejs is needed, please ensure it is loaded on the page.'
        );
      }
      const conf: { paths: { [key: string]: string } } = { paths: {} };

      // First, try to resolve with the CDN.
      // We default to the previous behavior
      // of trying for a full path. NOTE: in the
      // future, we should let the CDN resolve itself
      // based on the package.json contents (the next
      // case below)
      const { packageRoot, pathGuess } = moduleNameToCDNUrl(
        moduleName,
        moduleVersion
      );
      conf.paths[moduleName] = `${packageRoot}${pathGuess}`;

      require.undef(failedId);
      require.config(conf);
      return requirePromise([`${moduleName}`]).catch(err => {
        // Next, if this also errors, we the root
        // and let the CDN decide
        conf.paths[moduleName] = `${packageRoot}?`; // NOTE: the `?` is added to avoid require appending a .js
        require.undef(failedId);
        require.config(conf);
      });
    }
  });
}
