// Copyright (c) Jupyter Development Team.
// Copyright (c) Voila Development Team.
// Distributed under the terms of the Modified BSD License.

const fs = require('fs-extra');
const path = require('path');
const webpack = require('webpack');
const merge = require('webpack-merge').default;
const { ModuleFederationPlugin } = webpack.container;
const glob = require('glob');
const Build = require('@jupyterlab/builder').Build;
const baseConfig = require('@jupyterlab/builder/lib/webpack.config.base');

const data = require('./package.json');

/**
 * A helper for filtering deprecated webpack loaders, to be replaced with assets
 */
function filterDeprecatedRule(rule) {
  if (typeof rule.use === 'string' && rule.use.match(/^(file|url)-loader/)) {
    return false;
  }
  return true;
}

baseConfig.module.rules = [
  {
    test: /\.json$/,
    use: ['json-loader'],
    type: 'javascript/auto'
  },
  ...baseConfig.module.rules.filter(filterDeprecatedRule)
];

const names = Object.keys(data.dependencies).filter(name => {
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
const style = path.resolve(__dirname, 'style.css');

fs.copySync(libDir, buildDir);
fs.copySync(style, path.resolve(buildDir, 'style.css'));

const distRoot = path.resolve(
  __dirname,
  '..',
  '..',
  'voila',
  'voilite',
  'static',
  'voila'
);

const topLevelBuild = path.resolve('build');

const extras = Build.ensureAssets({
  packageNames: names,
  output: buildDir,
  themeOutput: path.resolve(distRoot)
});

// Make a bootstrap entrypoint
const entryPoint = path.join(buildDir, 'bootstrap.js');

if (process.env.NODE_ENV === 'production') {
  baseConfig.mode = 'production';
}

class CompileSchemasPlugin {
  apply(compiler) {
    compiler.hooks.done.tapAsync(
      'CompileSchemasPlugin',
      (compilation, callback) => {
        // ensure all schemas are statically compiled
        const schemaDir = path.resolve(topLevelBuild, './schemas');
        const files = glob.sync(`${schemaDir}/**/*.json`, {
          ignore: [`${schemaDir}/all.json`]
        });
        const all = files.map(file => {
          const schema = fs.readJSONSync(file);
          const pluginFile = file.replace(`${schemaDir}/`, '');
          const basename = path.basename(pluginFile, '.json');
          const dirname = path.dirname(pluginFile);
          const packageJsonFile = path.resolve(
            schemaDir,
            dirname,
            'package.json.orig'
          );
          const packageJson = fs.readJSONSync(packageJsonFile);
          const pluginId = `${dirname}:${basename}`;
          return {
            id: pluginId,
            raw: '{}',
            schema,
            settings: {},
            version: packageJson.version
          };
        });
        const distDir = path.resolve(distRoot, 'schemas');
        fs.mkdirSync(distDir, { recursive: true });
        fs.writeFileSync(
          path.resolve(distDir, 'all.json'),
          JSON.stringify(all)
        );
        callback();
      }
    );
  }
}

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
      filename: 'voilite.js'
    },
    module: {
      rules: [
        // just keep the woff2 fonts from fontawesome
        {
          test: /fontawesome-free.*\.(svg|eot|ttf|woff)$/,
          loader: 'ignore-loader'
        },
        {
          test: /\.(jpe?g|png|gif|ico|eot|ttf|map|woff2?)(\?v=\d+\.\d+\.\d+)?$/i,
          type: 'asset/resource'
        }
      ]
    },
    plugins: [
      new webpack.DefinePlugin({
        // Needed for Blueprint. See https://github.com/palantir/blueprint/issues/4393
        'process.env': '{}',
        // Needed for various packages using cwd(), like the path polyfill
        process: { cwd: () => '/' }
      }),
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: {
          ...data.dependencies
        }
      }),
      new CompileSchemasPlugin()
    ]
  })
].concat(extras);
