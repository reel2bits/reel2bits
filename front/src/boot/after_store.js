// Snippets from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/boot/after_store.js

import Vue from 'vue'
import router from '../router'
import App from '../App.vue'
import axios from 'axios'
import apiService from '../services/api/api.service.js'
import { getOrCreateApp, getClientToken } from '../backend/oauth/oauth.js'

const getNodeInfo = async ({ store }) => {
  await axios.get(`${store.state.instance.instanceUrl}/nodeinfo/2.0`)
    .then(function (res) {
      const data = res.data

      const metadata = data.metadata
      store.dispatch('setInstanceOption', { name: 'registrationOpen', value: metadata.openRegistrations })
      store.dispatch('setInstanceOption', { name: 'name', value: metadata.nodeName })
      store.dispatch('setInstanceOption', { name: 'description', value: metadata.nodeDescription })

      const software = data.software
      store.dispatch('setInstanceOption', { name: 'backendVersion', value: software.version })

      const frontendVersion = 'FIXME'
      store.dispatch('setInstanceOption', { name: 'frontendVersion', value: frontendVersion })
    })
    .catch(function (e) {
      console.warn('Could not load nodeinfo')
      console.warn(e)
    })
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
  })
}

const getAppSecret = async ({ store }) => {
  const { state, commit } = store
  const { oauth, instance } = state
  return getOrCreateApp({ ...oauth, instance: instance.instanceUrl, commit })
    .then((app) => getClientToken({ ...app, instance: instance.instanceUrl }))
    .then((token) => {
      commit('setAppToken', token.access_token)
    })
}

const setSettings = async ({ store }) => {
  const env = process.env.NODE_ENV
  if (env === 'development') {
    console.warn('OVERRIDING API CONFIG')
    // store.dispatch('setInstanceOption', { name: 'instanceUrl', value: 'http://localhost:5000' })
    store.dispatch('setInstanceOption', { name: 'instanceUrl', value: 'https://reel2bits.dev.lan.sigpipe.me' })
  } else {
    // FIXME
    throw new Error('IMPLEMENT ME')
  }

  apiService.setBaseUrl(store.state.instance.instanceUrl)
}

const getTOS = async ({ store }) => {
  try {
    // TODO: axios
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

const afterStoreSetup = ({ store }) => {
  Promise.all([
    setSettings({ store }), // set the right baseURL/instanceUrl
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
