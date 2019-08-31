// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

// TODO adapt to r2b
// Rename to notifications
// We don't care about the pure statuses part, only notifications
// But we might still use masto-statuses for notifications

import { remove, slice, each, findIndex, find, maxBy, minBy, merge, first, last, isArray, omitBy } from 'lodash'
import { set } from 'vue'
import apiService from '../services/api/api.service.js'
// import parse from '../services/status_parser/status_parser.js'

const emptyTl = (userId = 0) => ({
  statuses: [],
  statusesObject: {},
  faves: [],
  visibleStatuses: [],
  visibleStatusesObject: {},
  newStatusCount: 0,
  maxId: 0,
  minId: 0,
  minVisibleId: 0,
  loading: false,
  followers: [],
  friends: [],
  userId,
  flushMarker: 0
})

const emptyNotifications = () => ({
  desktopNotificationSilence: true,
  maxId: 0,
  minId: Number.POSITIVE_INFINITY,
  data: [],
  idStore: {},
  loading: false,
  error: false
})

export const defaultState = () => ({
  allStatuses: [],
  allStatusesObject: {},
  conversationsObject: {},
  maxId: 0,
  notifications: emptyNotifications(),
  favorites: new Set(),
  error: false,
  timelines: {
    mentions: emptyTl(),
    public: emptyTl(),
    user: emptyTl(),
    favorites: emptyTl(),
    media: emptyTl(),
    publicAndExternal: emptyTl(),
    friends: emptyTl(),
    tag: emptyTl(),
    dms: emptyTl()
  }
})

export const prepareStatus = (status) => {
  // Set deleted flag
  status.deleted = false

  // To make the array reactive
  status.attachments = status.attachments || []

  return status
}

const visibleNotificationTypes = (rootState) => {
  return [
    rootState.config.notificationVisibility.likes && 'like',
    rootState.config.notificationVisibility.mentions && 'mention',
    rootState.config.notificationVisibility.repeats && 'repeat',
    rootState.config.notificationVisibility.follows && 'follow'
  ].filter(_ => _)
}

const mergeOrAdd = (arr, obj, item) => {
  const oldItem = obj[item.id]

  if (oldItem) {
    // We already have this, so only merge the new info.
    // We ignore null values to avoid overwriting existing properties with missing data
    // we also skip 'user' because that is handled by users module
    merge(oldItem, omitBy(item, (v, k) => v === null || k === 'user'))
    // Reactivity fix.
    oldItem.attachments.splice(oldItem.attachments.length)
    return { item: oldItem, new: false }
  } else {
    // This is a new item, prepare it
    prepareStatus(item)
    arr.push(item)
    set(obj, item.id, item)
    return { item, new: true }
  }
}

const sortById = (a, b) => {
  const seqA = Number(a.id)
  const seqB = Number(b.id)
  const isSeqA = !Number.isNaN(seqA)
  const isSeqB = !Number.isNaN(seqB)
  if (isSeqA && isSeqB) {
    return seqA > seqB ? -1 : 1
  } else if (isSeqA && !isSeqB) {
    return 1
  } else if (!isSeqA && isSeqB) {
    return -1
  } else {
    return a.id > b.id ? -1 : 1
  }
}

const sortTimeline = (timeline) => {
  timeline.visibleStatuses = timeline.visibleStatuses.sort(sortById)
  timeline.statuses = timeline.statuses.sort(sortById)
  timeline.minVisibleId = (last(timeline.visibleStatuses) || {}).id
  return timeline
}

// Add status to the global storages (arrays and objects maintaining statuses) except timelines
const addStatusToGlobalStorage = (state, data) => {
  const result = mergeOrAdd(state.allStatuses, state.allStatusesObject, data)
  if (result.new) {
    // Add to conversation
    const status = result.item
    const conversationsObject = state.conversationsObject
    const conversationId = status.statusnet_conversation_id
    if (conversationsObject[conversationId]) {
      conversationsObject[conversationId].push(status)
    } else {
      set(conversationsObject, conversationId, [status])
    }
  }
  return result
}

// Remove status from the global storages (arrays and objects maintaining statuses) except timelines
const removeStatusFromGlobalStorage = (state, status) => {
  remove(state.allStatuses, { id: status.id })

  // TODO: Need to remove from allStatusesObject?

  // Remove possible notification
  remove(state.notifications.data, ({ action: { id } }) => id === status.id)

  // Remove from conversation
  const conversationId = status.statusnet_conversation_id
  if (state.conversationsObject[conversationId]) {
    remove(state.conversationsObject[conversationId], { id: status.id })
  }
}

const addNewStatuses = (state, { statuses, showImmediately = false, timeline, user = {},
  noIdUpdate = false, userId }) => {
  // Sanity check
  if (!isArray(statuses)) {
    return false
  }

  const allStatuses = state.allStatuses
  const timelineObject = state.timelines[timeline]

  const maxNew = statuses.length > 0 ? maxBy(statuses, 'id').id : 0
  const minNew = statuses.length > 0 ? minBy(statuses, 'id').id : 0
  const newer = timeline && (maxNew > timelineObject.maxId || timelineObject.maxId === 0) && statuses.length > 0
  const older = timeline && (minNew < timelineObject.minId || timelineObject.minId === 0) && statuses.length > 0

  if (!noIdUpdate && newer) {
    timelineObject.maxId = maxNew
  }
  if (!noIdUpdate && older) {
    timelineObject.minId = minNew
  }

  // This makes sure that user timeline won't get data meant for other
  // user. I.e. opening different user profiles makes request which could
  // return data late after user already viewing different user profile
  if ((timeline === 'user' || timeline === 'media') && timelineObject.userId !== userId) {
    return
  }

  const addStatus = (data, showImmediately, addToTimeline = true) => {
    const result = addStatusToGlobalStorage(state, data)
    const status = result.item

    if (result.new) {
      // We are mentioned in a post
      if (status.type === 'status' && find(status.attentions, { id: user.id })) {
        const mentions = state.timelines.mentions

        // Add the mention to the mentions timeline
        if (timelineObject !== mentions) {
          mergeOrAdd(mentions.statuses, mentions.statusesObject, status)
          mentions.newStatusCount += 1

          sortTimeline(mentions)
        }
      }
      if (status.visibility === 'direct') {
        const dms = state.timelines.dms

        mergeOrAdd(dms.statuses, dms.statusesObject, status)
        dms.newStatusCount += 1

        sortTimeline(dms)
      }
    }

    // Decide if we should treat the status as new for this timeline.
    let resultForCurrentTimeline
    // Some statuses should only be added to the global status repository.
    if (timeline && addToTimeline) {
      resultForCurrentTimeline = mergeOrAdd(timelineObject.statuses, timelineObject.statusesObject, status)
    }

    if (timeline && showImmediately) {
      // Add it directly to the visibleStatuses, don't change
      // newStatusCount
      mergeOrAdd(timelineObject.visibleStatuses, timelineObject.visibleStatusesObject, status)
    } else if (timeline && addToTimeline && resultForCurrentTimeline.new) {
      // Just change newStatuscount
      timelineObject.newStatusCount += 1
    }

    return status
  }

  const favoriteStatus = (favorite, counter) => {
    const status = find(allStatuses, { id: favorite.in_reply_to_status_id })
    if (status) {
      // This is our favorite, so the relevant bit.
      if (favorite.user.id === user.id) {
        status.favorited = true
      } else {
        status.fave_num += 1
      }
    }
    return status
  }

  const processors = {
    'status': (status) => {
      addStatus(status, showImmediately)
    },
    'retweet': (status) => {
      // RetweetedStatuses are never shown immediately
      const retweetedStatus = addStatus(status.retweeted_status, false, false)

      let retweet
      // If the retweeted status is already there, don't add the retweet
      // to the timeline.
      if (timeline && find(timelineObject.statuses, (s) => {
        if (s.retweeted_status) {
          return s.id === retweetedStatus.id || s.retweeted_status.id === retweetedStatus.id
        } else {
          return s.id === retweetedStatus.id
        }
      })) {
        // Already have it visible (either as the original or another RT), don't add to timeline, don't show.
        retweet = addStatus(status, false, false)
      } else {
        retweet = addStatus(status, showImmediately)
      }

      retweet.retweeted_status = retweetedStatus
    },
    'favorite': (favorite) => {
      // Only update if this is a new favorite.
      // Ignore our own favorites because we get info about likes as response to like request
      if (!state.favorites.has(favorite.id)) {
        state.favorites.add(favorite.id)
        favoriteStatus(favorite)
      }
    },
    'deletion': (deletion) => {
      const uri = deletion.uri
      const status = find(allStatuses, { uri })
      if (!status) {
        return
      }

      removeStatusFromGlobalStorage(state, status)

      if (timeline) {
        remove(timelineObject.statuses, { uri })
        remove(timelineObject.visibleStatuses, { uri })
      }
    },
    'follow': (follow) => {
      // NOOP, it is known status but we don't do anything about it for now
    },
    'default': (unknown) => {
      console.log('unknown status type')
      console.log(unknown)
    }
  }

  each(statuses, (status) => {
    const type = status.type
    const processor = processors[type] || processors['default']
    processor(status)
  })

  // Keep the visible statuses sorted
  if (timeline) {
    sortTimeline(timelineObject)
  }
}

const addNewNotifications = (state, { dispatch, notifications, older, visibleNotificationTypes, rootGetters }) => {
  each(notifications, (notification) => {
    if (notification.type !== 'follow') {
      notification.action = addStatusToGlobalStorage(state, notification.action).item
      notification.status = notification.status && addStatusToGlobalStorage(state, notification.status).item
    }

    // Only add a new notification if we don't have one for the same action
    if (!state.notifications.idStore.hasOwnProperty(notification.id)) {
      state.notifications.maxId = notification.id > state.notifications.maxId
        ? notification.id
        : state.notifications.maxId
      state.notifications.minId = notification.id < state.notifications.minId
        ? notification.id
        : state.notifications.minId

      state.notifications.data.push(notification)
      state.notifications.idStore[notification.id] = notification

      if ('Notification' in window && window.Notification.permission === 'granted') {
        const notifObj = {}
        const status = notification.status
        const title = notification.from_profile.name
        notifObj.icon = notification.from_profile.profile_image_url
        let i18nString
        switch (notification.type) {
          case 'like':
            i18nString = 'favorited_you'
            break
          case 'repeat':
            i18nString = 'repeated_you'
            break
          case 'follow':
            i18nString = 'followed_you'
            break
        }

        if (i18nString) {
          notifObj.body = rootGetters.i18n.t('notifications.' + i18nString)
        } else {
          notifObj.body = notification.status.text
        }

        // Shows first attached non-nsfw image, if any. Should add configuration for this somehow...
        if (status && status.attachments && status.attachments.length > 0 && !status.nsfw &&
          status.attachments[0].mimetype.startsWith('image/')) {
          notifObj.image = status.attachments[0].url
        }

        if (!notification.seen && !state.notifications.desktopNotificationSilence && visibleNotificationTypes.includes(notification.type)) {
          let notification = new window.Notification(title, notifObj)
          // Chrome is known for not closing notifications automatically
          // according to MDN, anyway.
          setTimeout(notification.close.bind(notification), 5000)
        }
      }
    } else if (notification.seen) {
      state.notifications.idStore[notification.id].seen = true
    }
  })
}

const removeStatus = (state, { timeline, userId }) => {
  const timelineObject = state.timelines[timeline]
  if (userId) {
    remove(timelineObject.statuses, { user: { id: userId } })
    remove(timelineObject.visibleStatuses, { user: { id: userId } })
    timelineObject.minVisibleId = timelineObject.visibleStatuses.length > 0 ? last(timelineObject.visibleStatuses).id : 0
    timelineObject.maxId = timelineObject.statuses.length > 0 ? first(timelineObject.statuses).id : 0
  }
}

export const mutations = {
  addNewStatuses,
  addNewNotifications,
  removeStatus,
  showNewStatuses (state, { timeline }) {
    const oldTimeline = (state.timelines[timeline])

    oldTimeline.newStatusCount = 0
    oldTimeline.visibleStatuses = slice(oldTimeline.statuses, 0, 50)
    oldTimeline.minVisibleId = last(oldTimeline.visibleStatuses).id
    oldTimeline.minId = oldTimeline.minVisibleId
    oldTimeline.visibleStatusesObject = {}
    each(oldTimeline.visibleStatuses, (status) => { oldTimeline.visibleStatusesObject[status.id] = status })
  },
  resetStatuses (state) {
    const emptyState = defaultState()
    Object.entries(emptyState).forEach(([key, value]) => {
      state[key] = value
    })
  },
  clearTimeline (state, { timeline, excludeUserId = false }) {
    const userId = excludeUserId ? state.timelines[timeline].userId : undefined
    state.timelines[timeline] = emptyTl(userId)
  },
  clearNotifications (state) {
    state.notifications = emptyNotifications()
  },
  setFavorited (state, { status, value }) {
    const newStatus = state.allStatusesObject[status.id]

    if (newStatus.favorited !== value) {
      if (value) {
        newStatus.fave_num++
      } else {
        newStatus.fave_num--
      }
    }

    newStatus.favorited = value
  },
  setFavoritedConfirm (state, { status, user }) {
    const newStatus = state.allStatusesObject[status.id]
    newStatus.favorited = status.favorited
    newStatus.fave_num = status.fave_num
    const index = findIndex(newStatus.favoritedBy, { id: user.id })
    if (index !== -1 && !newStatus.favorited) {
      newStatus.favoritedBy.splice(index, 1)
    } else if (index === -1 && newStatus.favorited) {
      newStatus.favoritedBy.push(user)
    }
  },
  setPinned (state, status) {
    const newStatus = state.allStatusesObject[status.id]
    newStatus.pinned = status.pinned
  },
  setMuted (state, status) {
    const newStatus = state.allStatusesObject[status.id]
    newStatus.muted = status.muted
  },
  setRetweeted (state, { status, value }) {
    const newStatus = state.allStatusesObject[status.id]

    if (newStatus.repeated !== value) {
      if (value) {
        newStatus.repeat_num++
      } else {
        newStatus.repeat_num--
      }
    }

    newStatus.repeated = value
  },
  setRetweetedConfirm (state, { status, user }) {
    const newStatus = state.allStatusesObject[status.id]
    newStatus.repeated = status.repeated
    newStatus.repeat_num = status.repeat_num
    const index = findIndex(newStatus.rebloggedBy, { id: user.id })
    if (index !== -1 && !newStatus.repeated) {
      newStatus.rebloggedBy.splice(index, 1)
    } else if (index === -1 && newStatus.repeated) {
      newStatus.rebloggedBy.push(user)
    }
  },
  setDeleted (state, { status }) {
    const newStatus = state.allStatusesObject[status.id]
    newStatus.deleted = true
  },
  setManyDeleted (state, condition) {
    Object.values(state.allStatusesObject).forEach(status => {
      if (condition(status)) {
        status.deleted = true
      }
    })
  },
  setLoading (state, { timeline, value }) {
    state.timelines[timeline].loading = value
  },
  setNsfw (state, { id, nsfw }) {
    const newStatus = state.allStatusesObject[id]
    newStatus.nsfw = nsfw
  },
  setError (state, { value }) {
    state.error = value
  },
  setNotificationsLoading (state, { value }) {
    state.notifications.loading = value
  },
  setNotificationsError (state, { value }) {
    state.notifications.error = value
  },
  setNotificationsSilence (state, { value }) {
    state.notifications.desktopNotificationSilence = value
  },
  markNotificationsAsSeen (state) {
    each(state.notifications.data, (notification) => {
      notification.seen = true
    })
  },
  queueFlush (state, { timeline, id }) {
    state.timelines[timeline].flushMarker = id
  },
  addRepeats (state, { id, rebloggedByUsers, currentUser }) {
    const newStatus = state.allStatusesObject[id]
    newStatus.rebloggedBy = rebloggedByUsers.filter(_ => _)
    // repeats stats can be incorrect based on polling condition, let's update them using the most recent data
    newStatus.repeat_num = newStatus.rebloggedBy.length
    newStatus.repeated = !!newStatus.rebloggedBy.find(({ id }) => currentUser.id === id)
  },
  addFavs (state, { id, favoritedByUsers, currentUser }) {
    const newStatus = state.allStatusesObject[id]
    newStatus.favoritedBy = favoritedByUsers.filter(_ => _)
    // favorites stats can be incorrect based on polling condition, let's update them using the most recent data
    newStatus.fave_num = newStatus.favoritedBy.length
    newStatus.favorited = !!newStatus.favoritedBy.find(({ id }) => currentUser.id === id)
  },
  updateStatusWithPoll (state, { id, poll }) {
    const status = state.allStatusesObject[id]
    status.poll = poll
  }
}

const statuses = {
  state: defaultState(),
  actions: {
    addNewStatuses ({ rootState, commit }, { statuses, showImmediately = false, timeline = false, noIdUpdate = false, userId }) {
      commit('addNewStatuses', { statuses, showImmediately, timeline, noIdUpdate, user: rootState.users.currentUser, userId })
    },
    addNewNotifications ({ rootState, commit, dispatch, rootGetters }, { notifications, older }) {
      commit('addNewNotifications', { visibleNotificationTypes: visibleNotificationTypes(rootState), dispatch, notifications, older, rootGetters })
    },
    setError ({ rootState, commit }, { value }) {
      commit('setError', { value })
    },
    setNotificationsLoading ({ rootState, commit }, { value }) {
      commit('setNotificationsLoading', { value })
    },
    setNotificationsError ({ rootState, commit }, { value }) {
      commit('setNotificationsError', { value })
    },
    setNotificationsSilence ({ rootState, commit }, { value }) {
      commit('setNotificationsSilence', { value })
    },
    deleteStatus ({ rootState, commit }, status) {
      commit('setDeleted', { status })
      apiService.deleteStatus({ id: status.id, credentials: rootState.users.currentUser.credentials })
    },
    markStatusesAsDeleted ({ commit }, condition) {
      commit('setManyDeleted', condition)
    },
    favorite ({ rootState, commit }, status) {
      // Optimistic favoriting...
      commit('setFavorited', { status, value: true })
      rootState.api.backendInteractor.favorite(status.id)
        .then(status => commit('setFavoritedConfirm', { status, user: rootState.users.currentUser }))
    },
    unfavorite ({ rootState, commit }, status) {
      // Optimistic unfavoriting...
      commit('setFavorited', { status, value: false })
      rootState.api.backendInteractor.unfavorite(status.id)
        .then(status => commit('setFavoritedConfirm', { status, user: rootState.users.currentUser }))
    },
    fetchPinnedStatuses ({ rootState, dispatch }, userId) {
      rootState.api.backendInteractor.fetchPinnedStatuses(userId)
        .then(statuses => dispatch('addNewStatuses', { statuses, timeline: 'user', userId, showImmediately: true, noIdUpdate: true }))
    },
    pinStatus ({ rootState, commit }, statusId) {
      return rootState.api.backendInteractor.pinOwnStatus(statusId)
        .then((status) => commit('setPinned', status))
    },
    unpinStatus ({ rootState, commit }, statusId) {
      rootState.api.backendInteractor.unpinOwnStatus(statusId)
        .then((status) => commit('setPinned', status))
    },
    muteConversation ({ rootState, commit }, statusId) {
      return rootState.api.backendInteractor.muteConversation(statusId)
        .then((status) => commit('setMuted', status))
    },
    unmuteConversation ({ rootState, commit }, statusId) {
      return rootState.api.backendInteractor.unmuteConversation(statusId)
        .then((status) => commit('setMuted', status))
    },
    retweet ({ rootState, commit }, status) {
      // Optimistic retweeting...
      commit('setRetweeted', { status, value: true })
      rootState.api.backendInteractor.retweet(status.id)
        .then(status => commit('setRetweetedConfirm', { status: status.retweeted_status, user: rootState.users.currentUser }))
    },
    unretweet ({ rootState, commit }, status) {
      // Optimistic unretweeting...
      commit('setRetweeted', { status, value: false })
      rootState.api.backendInteractor.unretweet(status.id)
        .then(status => commit('setRetweetedConfirm', { status, user: rootState.users.currentUser }))
    },
    queueFlush ({ rootState, commit }, { timeline, id }) {
      commit('queueFlush', { timeline, id })
    },
    markNotificationsAsSeen ({ rootState, commit }) {
      commit('markNotificationsAsSeen')
      apiService.markNotificationsAsSeen({
        id: rootState.statuses.notifications.maxId,
        credentials: rootState.users.currentUser.credentials
      })
    },
    fetchFavsAndRepeats ({ rootState, commit }, id) {
      Promise.all([
        rootState.api.backendInteractor.fetchFavoritedByUsers(id),
        rootState.api.backendInteractor.fetchRebloggedByUsers(id)
      ]).then(([favoritedByUsers, rebloggedByUsers]) => {
        commit('addFavs', { id, favoritedByUsers, currentUser: rootState.users.currentUser })
        commit('addRepeats', { id, rebloggedByUsers, currentUser: rootState.users.currentUser })
      })
    },
    fetchFavs ({ rootState, commit }, id) {
      rootState.api.backendInteractor.fetchFavoritedByUsers(id)
        .then(favoritedByUsers => commit('addFavs', { id, favoritedByUsers, currentUser: rootState.users.currentUser }))
    },
    fetchRepeats ({ rootState, commit }, id) {
      rootState.api.backendInteractor.fetchRebloggedByUsers(id)
        .then(rebloggedByUsers => commit('addRepeats', { id, rebloggedByUsers, currentUser: rootState.users.currentUser }))
    },
    search (store, { q, resolve, limit, offset, following }) {
      return store.rootState.api.backendInteractor.search2({ q, resolve, limit, offset, following })
        .then((data) => {
          store.commit('addNewUsers', data.accounts)
          store.commit('addNewStatuses', { statuses: data.statuses })
          return data
        })
    }
  },
  mutations
}

export default statuses
