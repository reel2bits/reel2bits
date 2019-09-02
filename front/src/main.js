import Vue from 'vue'
import Vuex from 'vuex'
import VueRouter from 'vue-router'
import BootstrapVue from 'bootstrap-vue'
import VueStringFilter from 'vue-string-filter'

import interfaceModule from './modules/interface.js'
import instanceModule from './modules/instance.js'
import statusesModule from './modules/statuses.js'
import usersModule from './modules/users.js'
import apiModule from './modules/api.js'
import configModule from './modules/config.js'
import tracksModule from './modules/tracks.js'
import albumsModule from './modules/albums.js'
import oauthModule from './modules/oauth.js'
import authFlowModule from './modules/auth_flow.js'

import VueI18n from 'vue-i18n'

import createPersistedState from './lib/persisted_state.js'

import afterStoreSetup from './boot/after_store.js'

import messages from './i18n/messages.js'

Vue.config.productionTip = false

const currentLocale = (window.navigator.language || 'en').split('-')[0]

Vue.use(Vuex)
Vue.use(VueRouter)
Vue.use(VueI18n)
Vue.use(BootstrapVue)
Vue.use(VueStringFilter)

const i18n = new VueI18n({
  // By default, use the browser locale, we will update it if neccessary
  locale: currentLocale,
  fallbackLocale: 'en',
  messages
})

const persistedStateOptions = {
  paths: [
    'config',
    'users.lastLoginName',
    'oauth'
  ]
};

(async () => {
  const persistedState = await createPersistedState(persistedStateOptions)
  const store = new Vuex.Store({
    modules: {
      i18n: {
        getters: {
          i18n: () => i18n
        }
      },
      interface: interfaceModule,
      instance: instanceModule,
      statuses: statusesModule,
      users: usersModule,
      api: apiModule,
      config: configModule,
      tracks: tracksModule,
      albums: albumsModule,
      oauth: oauthModule,
      authFlow: authFlowModule
    },
    plugins: [persistedState],
    strict: false
  })

  afterStoreSetup({ store, i18n })
})()

// These are inlined by webpack's DefinePlugin
/* eslint-disable */
window.___reel2bitsfe_mode = process.env
window.___reel2bitsfe_commit_hash = COMMIT_HASH
window.___reel2bitsfe_dev_overrides = DEV_OVERRIDES