import Vue from 'vue'

const defaultState = {
  registrationOpen: true,
  name: 'reel2bits',
  description: 'A reel2bits instance',
  backendVersion: '',
  frontendVersion: '',
  instanceUrl: '',
  tos: ''
}

const instance = {
  state: defaultState,
  mutations: {
    setInstanceOption (state, { name, value }) {
      if (typeof value !== 'undefined') {
        Vue.set(state, name, value)
      }
    }
  },
  actions: {
    setInstanceOption ({ commit, dispatch }, { name, value }) {
      commit('setInstanceOption', { name, value })
      switch (name) {
        case 'name':
          dispatch('setPageTitle')
          break
      }
    }
  }
}

export default instance
