// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

var merge = require('webpack-merge')
var prodEnv = require('./prod.env')

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"'
})
