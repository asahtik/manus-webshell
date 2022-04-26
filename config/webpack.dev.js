const path = require('path');
const webpack = require('webpack');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const FaviconsWebpackPlugin = require('favicons-webpack-plugin');

var metadata = require('../package.json');

var root = process.env.PWD;
var output = process.env.BUILD_DIRECTORY || path.resolve(root, "build", "frontend");

module.exports = {
    mode: "development",
    devtool: "source-map",
    devServer: {
        compress: true,
        port: parseInt(process.env.PORT || "8080"),
        client: {
          webSocketURL: 'auto://0.0.0.0:8081/ws',
        },
        host: '0.0.0.0',
        hot: true,
        static: {
          directory:  path.resolve(root, "manus_webshell", "frontend", "assets"),
        }
    },
    entry: {
        "app": path.resolve(root, "manus_webshell", "frontend", "main.js"),
    },
    output: {
      path: output,
      filename: "[name].js",
      publicPath: "/", // string
      library: { // There is also an old syntax for this available (click to show)
        type: "umd", // universal module definition
        name: "app",
      },
    },
    plugins: [
        new webpack.ProvidePlugin({
           $: "jquery",
           jQuery: "jquery"
        }),
        new HtmlWebpackPlugin({
          title: 'Manus',
          chunks: ['app'],
        }),
        new FaviconsWebpackPlugin(path.resolve(root, "manus_webshell", "frontend", "assets", "icon.png")),
        new webpack.DefinePlugin({
           VERSION: JSON.stringify(metadata.version + " (dev)")
        }),
      ],
    module:{
        rules: [
          { test: /\.handlebars$/, loader: "handlebars-loader", options: {runtime: path.resolve(root, 'config', 'handlebars')} },
          { test: /\.css$/, use: ["style-loader", "css-loader"], },
          {
            test: /\.(png|svg|jpg|jpeg|gif)$/i,
            type: 'asset/resource',
          },
          {
           test: /\.(woff|woff2|eot|ttf|otf)$/i,
           type: 'asset/resource',
         }
        ]
      }
  };

  console.log(path.resolve(root, 'node_modules/bootstrap-icons/font/fonts'));