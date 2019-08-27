// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

import { camelCase } from 'lodash'

import apiService from '../api/api.service.js'

const update = ({ store, statuses, timeline, showImmediately, userId }) => {
  const ccTimeline = camelCase(timeline)

  store.dispatch('setError', { value: false })

  store.dispatch('addNewStatuses', {
    timeline: ccTimeline,
    userId,
    statuses,
    showImmediately
  })
}

const fetchAndUpdate = ({ store, credentials, timeline = 'friends', older = false, showImmediately = false, userId = false, tag = false, until }) => {
  const args = { timeline, credentials }
  const rootState = store.rootState || store.state
  const timelineData = rootState.statuses.timelines[camelCase(timeline)]
  const hideMutedPosts = typeof rootState.config.hideMutedPosts === 'undefined'
    ? rootState.instance.hideMutedPosts
    : rootState.config.hideMutedPosts

  if (older) {
    args['until'] = until || timelineData.minId
  } else {
    args['since'] = timelineData.maxId
  }

  args['userId'] = userId
  args['tag'] = tag
  args['withMuted'] = !hideMutedPosts

  const numStatusesBeforeFetch = timelineData.statuses.length

  return apiService.fetchTimeline(args)
    .then((statuses) => {
      if (!older && statuses.length >= 20 && !timelineData.loading && numStatusesBeforeFetch > 0) {
        store.dispatch('queueFlush', { timeline: timeline, id: timelineData.maxId })
      }
      update({ store, statuses, timeline, showImmediately, userId })
      return statuses
    }, () => store.dispatch('setError', { value: true }))
}

const startFetching = ({ timeline = 'friends', credentials, store, userId = false, tag = false }) => {
  const rootState = store.rootState || store.state
  const timelineData = rootState.statuses.timelines[camelCase(timeline)]
  const showImmediately = timelineData.visibleStatuses.length === 0
  timelineData.userId = userId
  fetchAndUpdate({ timeline, credentials, store, showImmediately, userId, tag })
  const boundFetchAndUpdate = () => fetchAndUpdate({ timeline, credentials, store, userId, tag })
  return setInterval(boundFetchAndUpdate, 10000)
}
const timelineFetcher = {
  fetchAndUpdate,
  startFetching
}

export default timelineFetcher
