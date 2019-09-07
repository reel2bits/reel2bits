import { each, merge } from 'lodash'
import apiService from '../services/api/api.service.js'
import { humanizeErrors } from './errors'
import vue from 'vue'
import backendInteractorService from '../services/backend_interactor_service/backend_interactor_service.js'

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
    vue.set(obj, item.id, item)
    if (item.screen_name && !item.screen_name.includes('@')) {
      vue.set(obj, item.screen_name.toLowerCase(), item)
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
  },
  updateUserRelationship (state, relationships) {
    relationships.forEach(relationship => {
      const user = state.usersObject[relationship.id]
      if (user) {
        user.follows_you = relationship.followed_by
        user.following = relationship.following
        user.muted = relationship.muting
        user.blocking = relationship.blocking
        user.subscribed = relationship.subscribing
      }
    })
  },
  // Because frontend doesn't have a reason to keep these stuff in memory
  // outside of viewing someones user profile.
  clearFriends (state, userId) {
    const user = state.usersObject[userId]
    if (user) {
      vue.set(user, 'friendIds', [])
    }
  },
  clearFollowers (state, userId) {
    const user = state.usersObject[userId]
    if (user) {
      vue.set(user, 'followerIds', [])
    }
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

export const getters = {
  findUser: state => query => {
    console.debug('findUser ' + query)
    const result = state.usersObject[query]
    // In case it's screen_name, we can try searching case-insensitive
    if (!result && typeof query === 'string') {
      return state.usersObject[query.toLowerCase()]
    }
    return result
  }
}

const users = {
  state: defaultState,
  mutations,
  getters,
  actions: {
    fetchUser (store, id) {
      console.debug('fetchUser ' + id)
      return store.rootState.api.backendInteractor.fetchUser({ id })
        .then((user) => {
          store.commit('addNewUsers', [user])
          return user
        })
    },
    fetchUserRelationship (store, id) {
      if (store.state.currentUser) {
        store.rootState.api.backendInteractor.fetchUserRelationship({ id })
          .then((relationships) => store.commit('updateUserRelationship', relationships))
      }
    },
    loginUser (store, accessToken) {
      return new Promise((resolve, reject) => {
        store.commit('beginLogin')
        apiService.verifyCredentials(accessToken, store)
          .then((data) => {
            if (!data.error) {
              const user = data
              user.credentials = accessToken
              user.blockIds = []
              user.muteIds = []
              store.commit('setCurrentUser', user)
              store.commit('addNewUsers', [user])

              // TODO: getNotificationPermission()
              // Set our new backend interactor
              store.commit('setBackendInteractor', backendInteractorService(accessToken))

              // Start fetching notifications
              store.dispatch('startFetchingNotifications')
            } else {
              const response = data.error
              // Authentication failed
              store.commit('endLogin')
              if (response.status === 401) {
                reject(Error('Wrong username or password'))
              } else {
                reject(Error('An error occured, please try again'))
              }
            }
            store.commit('endLogin')
            resolve()
          })
          .catch((error) => {
            console.log(error)
            store.commit('endLogin')
            reject(Error('Failed to connect to server, try again'))
          })
      })
    },
    async signUp (store, userInfo) {
      console.debug('users:signUp')
      store.commit('signUpPending')

      try {
        let data = await apiService.register(userInfo, store)
        store.commit('signUpSuccess')
        store.commit('setToken', data.access_token)
        store.dispatch('loginUser', data.access_token)
      } catch (e) {
        let errors = JSON.parse(e.message)
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
      store.dispatch('stopFetching', 'friends')
      store.commit('setBackendInteractor', backendInteractorService(store.getters.getToken()))
      store.dispatch('stopFetching', 'notifications')
      store.commit('clearNotifications')
      store.commit('resetStatuses')
    }
  }
}

export default users
