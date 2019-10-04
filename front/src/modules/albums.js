import apiService from '../services/api/api.service.js'
import { humanizeErrors } from '../services/errors/registration_error.js'

export const mutations = {
  createPending (state) {
    state.createPending = true
    state.createErrors = []
  },
  createSuccess (state, data) {
    state.createPending = false
    state.albumId = data.id
    state.albumSlug = data.slug
  },
  createFailure (state, errors) {
    state.createPending = false
    state.createErrors = errors
  }
}

export const defaultState = {
  createPending: false,
  createErrors: [],
  albumId: null,
  albumSlug: null
}

export const getters = {
}

const albums = {
  state: defaultState,
  mutations,
  getters,
  actions: {
    async albumNew (store, albumInfo) {
      store.commit('createPending')

      try {
        let data = await apiService.albumNew(albumInfo, store)
        store.commit('createSuccess', data)
      } catch (e) {
        let errors = JSON.parse(e.message)

        if (typeof errors === 'object') {
          errors = humanizeErrors(errors)
        }

        store.commit('createFailure', errors)

        throw Error(errors)
      }
    }
  }
}

export default albums
