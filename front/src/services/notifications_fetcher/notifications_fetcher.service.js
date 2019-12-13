// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

// TODO adapt to r2b

import apiService from '../api/api.service.js'

const update = ({ store, notifications, older }) => {
  store.dispatch('setNotificationsError', { value: false })

  store.dispatch('addNewNotifications', { notifications, older })
}

const fetchAndUpdate = ({ store, credentials, older = false }) => {
  const args = { credentials }
  const rootState = store.rootState || store.state
  const timelineData = rootState.statuses.notifications

  args.timeline = 'notifications'
  if (older) {
    if (timelineData.minId !== Number.POSITIVE_INFINITY) {
      args.until = timelineData.minId
    }
    return fetchNotifications({ store, args, older })
  } else {
    // fetch new notifications
    if (timelineData.maxId !== Number.POSITIVE_INFINITY) {
      args.since = timelineData.maxId
    }
    const result = fetchNotifications({ store, args, older })

    // load unread notifications repeatedly to provide consistency between browser tabs
    const notifications = timelineData.data
    const unread = notifications.filter(n => !n.seen).map(n => n.id)
    if (unread.length) {
      args.since = Math.min(...unread)
      fetchNotifications({ store, args, older })
    }

    return result
  }
}

const fetchNotifications = ({ store, args, older }) => {
  return apiService.fetchTimeline(args)
    .then((notifications) => {
      update({ store, notifications, older })
      return notifications
    }, () => store.dispatch('setNotificationsError', { value: true }))
    .catch(() => store.dispatch('setNotificationsError', { value: true }))
}

const startFetching = ({ credentials, store }) => {
  fetchAndUpdate({ credentials, store })
  const boundFetchAndUpdate = () => fetchAndUpdate({ credentials, store })
  // Initially there's set flag to silence all desktop notifications so
  // that there won't spam of them when user just opened up the FE we
  // reset that flag after a while to show new notifications once again.
  setTimeout(() => store.dispatch('setNotificationsSilence', false), 10000)
  return setInterval(boundFetchAndUpdate, 10000)
}

const notificationsFetcher = {
  fetchAndUpdate,
  startFetching
}

export default notificationsFetcher
