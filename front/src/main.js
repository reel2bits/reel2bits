import Vue from 'vue'
import Vuex from 'vuex'
import VueRouter from 'vue-router'
import BootstrapVue from 'bootstrap-vue'

import interfaceModule from './modules/interface.js'
import instanceModule from './modules/instance.js'
import usersModule from './modules/users.js'
import tracksModule from './modules/tracks.js'
import albumsModule from './modules/albums.js'
import oauthModule from './modules/oauth.js'
import authFlowModule from './modules/auth_flow.js'

import createPersistedState from './lib/persisted_state.js'

import afterStoreSetup from './boot/after_store.js'

Vue.config.productionTip = false

Vue.use(Vuex)
Vue.use(VueRouter)
Vue.use(BootstrapVue)

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
      users: usersModule,
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