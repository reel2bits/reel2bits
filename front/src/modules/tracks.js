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
    async uploadTrack (store, trackInfo) {
      store.commit('uploadPending')
      console.log(1, store)
      try {
        let data = await apiService.trackUpload(trackInfo, store)
        console.log(data)
        console.log(2, store)
        store.commit('uploadSuccess')
      } catch (e) {
        let errors = e.message
        if (typeof errors === 'object') {
          errors = humanizeErrors(errors)
        }
        console.log(3, store)
        store.commit('uploadFailure', errors)
        throw Error(errors)
      }
    }
  }
}

export default tracks
