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

module.exports = [
  merge(baseConfig, {
    mode: 'development',
    entry: ['./publicpath.js', './' + path.relative(__dirname, entryPoint)],
    output: {
      path: distRoot,
      library: {
        type: 'var',
        name: ['_JUPYTERLAB', 'CORE_OUTPUT']
      },
      filename: 'voila.js'
    },
    plugins: [
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: {
          ...data.dependencies
        }
      })
    ]
  }),
  merge(baseConfig, {
    entry: './' + path.relative(__dirname, styleEntryPoint),
    mode: 'production',
    output: {
      path: distRoot,
      filename: 'voila-style.js'
    }
  })
].concat(extras);
