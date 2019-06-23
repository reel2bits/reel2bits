// Snippets from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/boot/after_store.js

import Vue from 'vue'
import router from '../router'
import App from '../App.vue'
import axios from 'axios'
import apiService from '../services/api/api.service.js'

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
    }
  })
}

const getAppSecret = async ({ store }) => {

}

const setSettings = async ({ store }) => {
  const env = process.env.NODE_ENV
  if (env === 'development') {
    console.warn('OVERRIDING API CONFIG')
    // store.dispatch('setInstanceOption', { name: 'instanceUrl', value: 'http://localhost:5000' })
    store.dispatch('setInstanceOption', { name: 'instanceUrl', value: 'https://reel2bits.dev.lan.sigpipe.me' })
  } else {
    throw new Error('IMPLEMENT ME')
  }

  apiService.setBaseUrl(store.state.instance.instanceUrl)

  getAppSecret({ store })
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
    checkOAuthToken({ store }),
    setSettings({ store }),
    getTOS({ store }),
    getNodeInfo({ store })
  ])

  return new Vue({
    router,
    store,
    el: '#app',
    render: h => h(App)
  })
}

export default afterStoreSetup
