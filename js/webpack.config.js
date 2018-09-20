
var path = require('path');
var postcss = require('postcss');

var loaders = [
    { test: /\.js$/, loader: 'babel-loader', query: {presets: ['es2015', 'stage-0']}, exclude: /node_modules/ },
    { test: /\.css$/, use: [
        'style-loader',
        'css-loader',
        {
            loader: 'postcss-loader',
            options: {
                plugins: [
                    postcss.plugin('delete-tilde', function() {
                        return function (css) {
                            css.walkAtRules('import', function(rule) {
                                rule.params = rule.params.replace('~', '');
                            });
                        };
                    }),
                    require('postcss-import')(),
                ]
            }
        }
    ]},
    // required to load font-awesome
    { test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/font-woff' },
    { test: /\.woff(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/font-woff' },
    { test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/octet-stream' },
    { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, use: 'file-loader' },
    { test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=image/svg+xml' }
]

var distRoot = path.resolve(__dirname, '..', 'voila', 'static')

module.exports = [
    {
        entry: ['babel-polyfill', './index.js'],
        output: {
            filename: 'libwidgets.js',
            path: distRoot,
            libraryTarget: 'amd'
        },
        module: { loaders: loaders },
        devtool: 'source-map'
    }
]
