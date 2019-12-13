// Snippets from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/boot/after_store.js

import Vue from 'vue'
import VueRouter from 'vue-router'
import routes from './routes'
import App from '../App.vue'
import { getOrCreateApp, getClientToken } from '../backend/oauth/oauth.js'
import backendInteractorService from '../services/backend_interactor_service/backend_interactor_service.js'

const getNodeInfo = async ({ store }) => {
  try {
    const res = await window.fetch('/nodeinfo/2.1')
    if (res.ok) {
      const data = await res.json()
      store.dispatch('setInstanceOption', { name: 'registrationOpen', value: data.openRegistrations })

      const metadata = data.metadata
      store.dispatch('setInstanceOption', { name: 'name', value: metadata.nodeName })
      store.dispatch('setInstanceOption', { name: 'description', value: metadata.nodeDescription })
      store.dispatch('setInstanceOption', { name: 'trackSizeLimit', value: metadata.uploadLimits.track })
      store.dispatch('setInstanceOption', { name: 'restrictedNicknames', value: metadata.restrictedNicknames })
      store.dispatch('setInstanceOption', { name: 'sentryDsn', value: metadata.sentryDsn })
      store.dispatch('setInstanceOption', { name: 'announcement', value: metadata.announcement })

      const software = data.software
      store.dispatch('setInstanceOption', { name: 'backendVersion', value: software.version })
      store.dispatch('setInstanceOption', { name: 'sourceUrl', value: software.repository })

      const frontendVersion = window.___reel2bitsfe_commit_hash
      store.dispatch('setInstanceOption', { name: 'frontendVersion', value: frontendVersion })
    } else {
      throw (res)
    }
  } catch (e) {
    console.warn('Could not load nodeinfo')
    console.warn(e)
  }
}

const checkOAuthToken = async ({ store }) => {
  return new Promise(async (resolve, reject) => {
    if (store.getters.getUserToken()) {
      try {
        await store.dispatch('loginUser', store.getters.getUserToken())
      } catch (e) {
        console.log(e)
      }
    } else {
      console.log('no user token present in cache')
    }
    resolve()
  })
}

const getAppSecret = async ({ store }) => {
  console.log('getAppSecret')
  const { state, commit } = store
  const { oauth } = state
  return getOrCreateApp({ ...oauth, commit })
    .then((app) => {
      if (app.ok) {
        getClientToken({ ...app })
      }
    })
    .then((token) => {
      if (token) {
        commit('setAppToken', token.access_token)
        commit('setBackendInteractor', backendInteractorService(store.getters.getToken()))
      }
    })
}

const getTOS = async ({ store }) => {
  try {
    const res = await window.fetch('/static/terms-of-service.html')
    if (res.ok) {
      const html = await res.text()
      store.dispatch('setInstanceOption', { name: 'tos', value: html })
    } else {
      throw (res)
    }
  } catch (e) {
    console.warn("Can't load TOS")
    console.warn(e)
  }
}

const afterStoreSetup = async ({ store }) => {
  await Promise.all([
    checkOAuthToken({ store }), // check token and try to log user if found
    getAppSecret({ store }), // try to get or create app and token thingy
    getTOS({ store }), // get the terms of service
    getNodeInfo({ store }) // fetch nodeinfo and feed infos in store
  ])
  // .catch(function (error) {
  //  console.log('Cannot init Frontend')
  //  console.log(error)
  //  throw new Error('Cannot initialize the frontend')
  // })

  const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: routes(store)
  })

  return new Vue({
    router,
    store,
    el: '#app',
    render: h => h(App)
  })
}

export default afterStoreSetup
