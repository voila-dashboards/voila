
var path = require('path');

var rules = [
    { test: /\.css$/, use: [
        'style-loader',
        'css-loader'
    ]},
    // required to load font-awesome
    { test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/font-woff&name=/voila/static/[hash].[ext]' },
    { test: /\.woff(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/font-woff&name=/voila/static/[hash].[ext]' },
    { test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=application/octet-stream&name=/voila/static/[hash].[ext]' },
    { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, use: 'file-loader&name=/voila/static/[hash].[ext]' },
    { test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, use: 'url-loader?limit=10000&mimetype=image/svg+xml&name=/voila/static/[hash].[ext]' }
]

var distRoot = path.resolve(__dirname, '..', 'share', 'jupyter', 'voila', 'templates', 'default', 'static')

module.exports = [
    {
        entry: ['./lib/index.js'],
        output: {
            filename: 'voila.js',
            path: distRoot,
            libraryTarget: 'amd'
        },
        module: { rules: rules },
        devtool: 'source-map'
    }
]
