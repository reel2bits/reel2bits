// Snippets from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/modules/auth_flow.js

const PASSWORD_STRATEGY = 'password'
const TOKEN_STRATEGY = 'token'

// initial state
const state = {
  app: null,
  settings: {},
  strategy: PASSWORD_STRATEGY,
  initStrategy: PASSWORD_STRATEGY // default strategy from config
}

const resetState = (state) => {
  state.strategy = state.initStrategy
  state.settings = {}
  state.app = null
}

// getters
const getters = {
  app: (state, getters) => {
    return state.app
  },
  settings: (state, getters) => {
    return state.settings
  },
  requiredPassword: (state, getters, rootState) => {
    return state.strategy === PASSWORD_STRATEGY
  },
  requiredToken: (state, getters, rootState) => {
    return state.strategy === TOKEN_STRATEGY
  }
}

// mutations
const mutations = {
  setInitialStrategy (state, strategy) {
    if (strategy) {
      state.initStrategy = strategy
      state.strategy = strategy
    }
  },
  requirePassword (state) {
    state.strategy = PASSWORD_STRATEGY
  },
  requireToken (state) {
    state.strategy = TOKEN_STRATEGY
  }
}

// actions
const actions = {
  // eslint-disable-next-line camelcase
  async login ({ state, dispatch, commit }, { access_token }) {
    commit('setToken', access_token, { root: true })
    await dispatch('loginUser', access_token, { root: true })
    resetState(state)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
