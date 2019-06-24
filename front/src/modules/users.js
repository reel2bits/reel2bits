import { each, merge } from 'lodash'
import apiService from '../services/api/api.service.js'
import { humanizeErrors } from './errors'

// Function from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/modules/users.js
export const mergeOrAdd = (arr, obj, item) => {
  if (!item) { return false }
  const oldItem = obj[item.id]
  if (oldItem) {
    // We already have this, so only merge the new info.
    merge(oldItem, item)
    return { item: oldItem, new: false }
  } else {
    // This is a new item, prepare it
    arr.push(item)
    this.$set(obj, item.id, item)
    if (item.screen_name && !item.screen_name.includes('@')) {
      this.$set(obj, item.screen_name.toLowerCase(), item)
    }
    return { item, new: true }
  }
}

export const mutations = {
  setCurrentUser (state, user) {
    state.lastLoginName = user.screen_name
    state.currentUser = merge(state.currentUser || {}, user)
  },
  addNewUsers (state, users) {
    each(users, (user) => mergeOrAdd(state.users, state.usersObject, user))
  },
  beginLogin (state) {
    state.loggingIn = true
  },
  endLogin (state) {
    state.loggingIn = false
  },
  signUpPending (state) {
    state.signUpPending = true
    state.signUpErrors = []
  },
  signUpSuccess (state) {
    state.signUpPending = false
  },
  signUpFailure (state, errors) {
    state.signUpPending = false
    state.signUpErrors = errors
  },
  clearCurrentUser (state) {
    state.currentUser = false
    state.lastLoginName = false
  }
}

export const defaultState = {
  loggingIn: false,
  currentUser: false,
  lastLoginName: false,
  users: [],
  usersObject: {},
  signUpPending: false,
  signUpErrors: []
}

const users = {
  state: defaultState,
  mutations,
  actions: {
    loginUser (store, accessToken) {
      return new Promise((resolve, reject) => {
        store.commit('beginLogin')
        apiService.verifyCredentials(accessToken)
          .then((data) => {
            if (!data.error) {
              const user = data
              user.credentials = accessToken
              store.commit('setCurrentUser', user)
              store.commit('addNewUsers', [user])

              // TODO: getNotificationPermission()
            } else {
              const response = data.error
              // Authentication failed
              store.commit('endLogin')
              if (response.status === 401) {
                reject('Wrong username or password')
              } else {
                reject('An error occured, please try again')
              }
            }
            store.commit('endLogin')
            resolve()
          })
          .catch((error) => {
            console.log(error)
            store.commit('endLogin')
            reject('Failed to connect to server, try again')
          })
      })
    },
    async signUp (store, userInfo) {
      store.commit('signUpPending')

      try {
        let data = await apiService.register(userInfo, store)
        store.commit('signUpSuccess')
        store.commit('setToken', data.access_token)
        store.dispatch('loginUser', data.access_token)
      } catch (e) {
        let errors = e.message
        // replace ap_id with username
        if (typeof errors === 'object') {
          if (errors.ap_id) {
            errors.username = errors.ap_id
            delete errors.ap_id
          }
          errors = humanizeErrors(errors)
        }
        store.commit('signUpFailure', errors)
        throw Error(errors)
      }
    },
    logout (store) {
      store.commit('clearCurrentUser')
      store.commit('clearToken')
    }
  }
}

export default users
