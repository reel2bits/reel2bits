import apiService from '../services/api/api.service.js'
import { humanizeErrors } from './errors'

export const mutations = {
  uploadPending (state) {
    state.uploadPending = true
    state.uploadErrors = []
  },
  uploadSuccess (state) {
    state.uploadPending = false
  },
  uploadFailure (state, errors) {
    state.uploadPending = false
    state.uploadErrors = errors
  }
}

export const defaultState = {
  uploadPending: false,
  uploadErrors: []
}

export const getters = {
}

const tracks = {
  state: defaultState,
  mutations,
  getters,
  actions: {
    async trackUpload (store, trackInfo) {
      store.commit('uploadPending')

      try {
        let data = await apiService.trackUpload(trackInfo, store)
        store.commit('uploadSuccess')
        store.commit('setToken', data.access_token)
        store.dispatch('loginUser', data.access_token)
      } catch (e) {
        let errors = e.message
        if (typeof errors === 'object') {
          errors = humanizeErrors(errors)
        }
        store.commit('uploadFailure', errors)
        throw Error(errors)
      }
    }
  }
}

export default tracks
