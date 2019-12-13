// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

import backendInteractorService from '../services/backend_interactor_service/backend_interactor_service.js'
import { Socket } from 'phoenix'

const api = {
  state: {
    backendInteractor: backendInteractorService(),
    fetchers: {},
    socket: null,
    followRequests: []
  },
  mutations: {
    setBackendInteractor (state, backendInteractor) {
      state.backendInteractor = backendInteractor
    },
    addFetcher (state, { fetcherName, fetcher }) {
      state.fetchers[fetcherName] = fetcher
    },
    removeFetcher (state, { fetcherName }) {
      delete state.fetchers[fetcherName]
    },
    setWsToken (state, token) {
      state.wsToken = token
    },
    setSocket (state, socket) {
      state.socket = socket
    },
    setFollowRequests (state, value) {
      state.followRequests = value
    }
  },
  actions: {
    startFetchingTimeline (store, { timeline = 'friends', tag = false, userId = false }) {
      // Don't start fetching if we already are.
      if (store.state.fetchers[timeline]) return

      const fetcher = store.state.backendInteractor.startFetchingTimeline({ timeline, store, userId, tag })
      store.commit('addFetcher', { fetcherName: timeline, fetcher })
    },
    startFetchingNotifications (store) {
      // Don't start fetching if we already are.
      if (store.state.fetchers.notifications) return

      const fetcher = store.state.backendInteractor.startFetchingNotifications({ store })
      store.commit('addFetcher', { fetcherName: 'notifications', fetcher })
    },
    stopFetching (store, fetcherName) {
      const fetcher = store.state.fetchers[fetcherName]
      window.clearInterval(fetcher)
      store.commit('removeFetcher', { fetcherName })
    },
    setWsToken (store, token) {
      store.commit('setWsToken', token)
    },
    initializeSocket ({ dispatch, commit, state, rootState }) {
      // Set up websocket connection
      const token = state.wsToken
      if (rootState.instance.chatAvailable && typeof token !== 'undefined' && state.socket === null) {
        const socket = new Socket('/socket', { params: { token } })
        socket.connect()

        commit('setSocket', socket)
        dispatch('initializeChat', socket)
      }
    },
    disconnectFromSocket ({ commit, state }) {
      state.socket && state.socket.disconnect()
      commit('setSocket', null)
    },
    removeFollowRequest (store, request) {
      const requests = store.state.followRequests.filter((it) => it !== request)
      store.commit('setFollowRequests', requests)
    }
  }
}

export default api
