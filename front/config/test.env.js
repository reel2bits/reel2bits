// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

var merge = require('webpack-merge')
var devEnv = require('./dev.env')

module.exports = merge(devEnv, {
  NODE_ENV: '"testing"'
})
