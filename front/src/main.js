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

import GetTextPlugin from 'vue-gettext'
import locales from './locales.js'

import createPersistedState from './lib/persisted_state.js'

import afterStoreSetup from './boot/after_store.js'

Vue.config.productionTip = false

let availableLanguages = (function () {
  let l = {}
  locales.locales.forEach(c => {
    l[c.code] = c.label
  })
  return l
})()
Vue.use(GetTextPlugin, {
  availableLanguages: availableLanguages,
  defaultLanguage: 'en_US',
  // cf https://github.com/Polyconseil/vue-gettext#configuration
  // not recommended but this is fixing weird bugs with translation nodes
  // not being updated when in v-if/v-else clauses
  autoAddKeyAttributes: true,
  languageVmMixin: {
    computed: {
      currentKebabCase: function () {
        return this.current.toLowerCase().replace('_', '-')
      }
    }
  },
  translations: {},
  silent: true
})

Vue.use(Vuex)
Vue.use(VueRouter)
Vue.use(BootstrapVue)
Vue.use(VueStringFilter)

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

  afterStoreSetup({ store })
})()

// These are inlined by webpack's DefinePlugin
/* eslint-disable */
window.___reel2bitsfe_mode = process.env
window.___reel2bitsfe_commit_hash = COMMIT_HASH
window.___reel2bitsfe_dev_overrides = DEV_OVERRIDES