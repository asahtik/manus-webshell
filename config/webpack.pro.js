const path = require('path');

const webpack = require('webpack');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const FaviconsWebpackPlugin = require('favicons-webpack-plugin');

var metadata = require('../package.json');

var root = process.env.PWD;
var output = process.env.BUILD_DIRECTORY || path.resolve(root, "build", "frontend");

module.exports = {
    mode: "production",
    entry: {
        "app": path.resolve(root, "manus_webshell", "frontend", "main.js"),
        },
    output: {
      path: output, // string (default)
      filename: "[name].js",
      publicPath: "./", // string
      library: { // There is also an old syntax for this available (click to show)
        type: "umd", // universal module definition
        name: "app",
      },
    },
    plugins: [
        new HtmlWebpackPlugin({
            title: 'Manus',
            chunks: ['app'],
        }),
        new FaviconsWebpackPlugin(path.resolve(root, "manus_webshell", "frontend", "assets", "icon.png")),
        new webpack.DefinePlugin({
           VERSION: JSON.stringify(metadata.version)
        })
      ],
    module:{
        rules: [
          { test: /\.handlebars$/, loader: "handlebars-loader", options: {runtime: path.resolve(root, "config", 'handlebars')} },
          { test: /\.css$/, use: ["style-loader", "css-loader"], },
          {  test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
            include: path.resolve(root, 'node_modules/bootstrap-icons/font/fonts'),
            use: {
                loader: 'file-loader',
                options: {
                    name: '[name].[ext]',
                    outputPath: 'webfonts',
                    publicPath: './webfonts',
                },
            }
          },
        ]
      }
  };
