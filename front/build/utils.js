// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

var path = require('path')
var config = require('../config')
var sass = require('sass')
var MiniCssExtractPlugin = require('mini-css-extract-plugin')

exports.assetsPath = function (_path) {
  var assetsSubDirectory = process.env.NODE_ENV === 'production'
      ? config.build.assetsSubDirectory
      : config.dev.assetsSubDirectory
  return path.posix.join(assetsSubDirectory, _path)
}

exports.cssLoaders = function (options) {
  options = options || {}

  function generateLoaders (loaders) {
    // Extract CSS when that option is specified
    // (which is the case during production build)
    if (options.extract) {
      return [MiniCssExtractPlugin.loader].concat(loaders)
    } else {
      return ['vue-style-loader'].concat(loaders)
    }
  }

  // http://vuejs.github.io/vue-loader/configurations/extract-css.html
  return [
    {
      test: /\.(post)?css$/,
      use: generateLoaders(['css-loader']),
    },
    {
      test: /\.less$/,
      use: generateLoaders(['css-loader', 'less-loader']),
    },
    {
      test: /\.sass$/,
      use: generateLoaders([
        'css-loader',
        {
          loader: 'sass-loader',
          options: {
            indentedSyntax: true
          }
        }
      ])
    },
    {
      test: /\.scss$/,
      use: generateLoaders(['css-loader', 'sass-loader'])
    },
    {
      test: /\.styl(us)?$/,
      use: generateLoaders(['css-loader', 'stylus-loader']),
    },
  ]
}

// Generate loaders for standalone style files (outside of .vue)
exports.styleLoaders = function (options) {
  return exports.cssLoaders(options)
}
