import apiService from '../services/api/api.service.js'
import { humanizeErrors } from '../services/errors/registration_error.js'

export const mutations = {
  uploadPending (state) {
    state.uploadPending = true
    state.uploadErrors = []
  },
  uploadSuccess (state, data) {
    state.uploadPending = false
    state.uploadId = data.id
    state.uploadSlug = data.slug
  },
  uploadFailure (state, errors) {
    state.uploadPending = false
    state.uploadErrors = errors
  }
}

export const defaultState = {
  uploadPending: false,
  uploadErrors: [],
  uploadId: null,
  uploadSlug: null
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

      try {
        const data = await apiService.trackUpload(trackInfo, store)
        store.commit('uploadSuccess', data)
      } catch (e) {
        let errors = JSON.parse(e.message)

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
