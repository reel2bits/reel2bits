// Snippets from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/boot/after_store.js

import Vue from 'vue'
import router from '../router'
import App from '../App.vue'
import { getOrCreateApp, getClientToken } from '../backend/oauth/oauth.js'

const getNodeInfo = async ({ store }) => {
  try {
    const res = await window.fetch(`/nodeinfo/2.0`)
    if (res.ok) {
      const data = await res.json()

      const metadata = data.metadata
      store.dispatch('setInstanceOption', { name: 'registrationOpen', value: metadata.openRegistrations })
      store.dispatch('setInstanceOption', { name: 'name', value: metadata.nodeName })
      store.dispatch('setInstanceOption', { name: 'description', value: metadata.nodeDescription })
      store.dispatch('setInstanceOption', { name: 'track_size_limit', value: 536807912 }) // FIXME TODO implement in backend

      const software = data.software
      store.dispatch('setInstanceOption', { name: 'backendVersion', value: software.version })

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
  const { state, commit } = store
  const { oauth } = state
  return getOrCreateApp({ ...oauth, commit })
    .then((app) => getClientToken({ ...app }))
    .then((token) => {
      commit('setAppToken', token.access_token)
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

  return new Vue({
    router,
    store,
    el: '#app',
    render: h => h(App)
  })
}

export default afterStoreSetup
