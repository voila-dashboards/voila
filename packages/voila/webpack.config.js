// Copyright (c) Jupyter Development Team.
// Copyright (c) Voila Development Team.
// Distributed under the terms of the Modified BSD License.

const fs = require('fs-extra');
const path = require('path');
const webpack = require('webpack');
const merge = require('webpack-merge').default;
const { ModuleFederationPlugin } = webpack.container;
const Build = require('@jupyterlab/builder').Build;
const baseConfig = require('@jupyterlab/builder/lib/webpack.config.base');

const data = require('./package.json');

const names = Object.keys(data.dependencies).filter((name) => {
  if (name === 'style-mod') {
    return false;
  }

  const packageData = require(path.join(name, 'package.json'));
  return packageData.jupyterlab !== undefined;
});

// Ensure a clear build directory.
const buildDir = path.resolve(__dirname, 'build');
if (fs.existsSync(buildDir)) {
  fs.removeSync(buildDir);
}
fs.ensureDirSync(buildDir);

// Copy files to the build directory
const libDir = path.resolve(__dirname, 'lib');
fs.copySync(libDir, buildDir);

const assetDir = path.resolve(
  __dirname,
  '..',
  '..',
  'share',
  'jupyter',
  'voila'
);
const extras = Build.ensureAssets({
  packageNames: names,
  output: assetDir
});

// Make a bootstrap entrypoint
const entryPoint = path.join(buildDir, 'bootstrap.js');
const treeEntryPoint = path.join(buildDir, 'treebootstrap.js');

// Also build the style bundle
const styleDir = path.resolve(__dirname, 'style');
const styleEntryPoint = path.join(styleDir, 'index.js');

if (process.env.NODE_ENV === 'production') {
  baseConfig.mode = 'production';
}

const distRoot = path.resolve(
  __dirname,
  '..',
  '..',
  'share',
  'jupyter',
  'voila',
  'templates',
  'base',
  'static'
);

const voilaIndexSharedPackages = {};
for (const dependency of Object.keys(data.dependencies)) {
  // Do not share jupyter-widgets packages in the Voila index
  if (
    [
      '@jupyter-widgets/base7',
      '@jupyter-widgets/base',
      '@jupyter-widgets/controls7',
      '@jupyter-widgets/controls'
    ].includes(
      dependency
    )
  ) {
    continue;
  }

  voilaIndexSharedPackages[dependency] = data.dependencies[dependency];
}

module.exports = [
  /*
   * Voila main index
   */
  merge(baseConfig, {
    mode: 'development',
    entry: {
      voila: ['./publicpath.js', './' + path.relative(__dirname, entryPoint)],
      treepage: [
        './publicpath.js',
        './' + path.relative(__dirname, treeEntryPoint)
      ]
    },
    output: {
      path: distRoot,
      library: {
        type: 'var',
        name: ['_JUPYTERLAB', 'CORE_OUTPUT']
      },
      filename: '[name].js',
      chunkFilename: '[name].voila.js'
    },
    plugins: [
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: voilaIndexSharedPackages
      })
    ],
    resolve: {
      fallback: {
        util: require.resolve('util/')
      }
    }
  }),
  /*
   * Voila styles
   */
  merge(baseConfig, {
    entry: './' + path.relative(__dirname, styleEntryPoint),
    mode: 'production',
    output: {
      path: distRoot,
      filename: 'voila-style.js'
    }
  }),
  /*
   * jupyter-widgets 7 packages
   */
  merge(baseConfig, {
    mode: 'development',
    entry: {
      ipywidgets7shared: ['./publicpath.js', './' + path.relative(__dirname, path.join(buildDir, 'ipywidgets7shared.js'))]
    },
    output: {
      path: distRoot,
      library: {
        type: 'var',
        name: ['_JUPYTERLAB', 'CORE_OUTPUT']
      },
      filename: '[name].js',
      chunkFilename: '[name].ipywidgets7shared.js'
    },
    plugins: [
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: {
          '@jupyter-widgets/base': data.dependencies['@jupyter-widgets/base7'],
          '@jupyter-widgets/controls': data.dependencies['@jupyter-widgets/controls7']
        }
      })
    ],
    resolve: {
      fallback: {
        util: require.resolve('util/')
      }
    }
  }),
  /*
   * jupyter-widgets 8 packages
   */
  merge(baseConfig, {
    mode: 'development',
    entry: {
      ipywidgets8shared: ['./publicpath.js', './' + path.relative(__dirname, path.join(buildDir, 'ipywidgets8shared.js'))]
    },
    output: {
      path: distRoot,
      library: {
        type: 'var',
        name: ['_JUPYTERLAB', 'CORE_OUTPUT']
      },
      filename: '[name].js',
      chunkFilename: '[name].ipywidgets8shared.js'
    },
    plugins: [
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: {
          '@jupyter-widgets/base': data.dependencies['@jupyter-widgets/base'],
          '@jupyter-widgets/controls': data.dependencies['@jupyter-widgets/controls']
        }
      })
    ],
    resolve: {
      fallback: {
        util: require.resolve('util/')
      }
    }
  }),
].concat(extras);
