import { parseUser, parseTrack, parseAlbum } from '../entity_normalizer/entity_normalizer.service.js'
import { StatusCodeError } from '../errors/errors'
import { map } from 'lodash'

const MASTODON_LOGIN_URL = '/api/v1/accounts/verify_credentials'
const MASTODON_REGISTRATION_URL = '/api/v1/accounts'
const MASTODON_USER_URL = '/api/v1/accounts'

const TRACKS_UPLOAD_URL = '/api/tracks'
const TRACKS_FETCH_URL = (username, id) => `/api/tracks/${username}/${id}`
const TRACKS_EDIT_URL = (username, id) => `/api/tracks/${username}/${id}`
const TRACKS_DELETE_URL = (username, id) => `/api/tracks/${username}/${id}`

const ALBUMS_NEW_URL = '/api/albums'
const ALBUMS_FETCH_URL = (username, id) => `/api/albums/${username}/${id}`
const ALBUMS_DELETE_URL = (username, id) => `/api/albums/${username}/${id}`

const ACCOUNT_LOGS_URL = (username, currentPage, perPage) => `/api/users/${username}/logs?page=${currentPage}&page_size=${perPage}`

const MASTODON_PUBLIC_TIMELINE = '/api/v1/timelines/public'
const MASTODON_USER_HOME_TIMELINE_URL = '/api/v1/timelines/home'
const MASTODON_DIRECT_MESSAGES_TIMELINE_URL = '/api/v1/timelines/direct'
const MASTODON_USER_NOTIFICATIONS_URL = '/api/v1/notifications'
const MASTODON_USER_TIMELINE_URL = id => `/api/v1/accounts/${id}/statuses`
const MASTODON_PROFILE_UPDATE_URL = '/api/v1/accounts/update_credentials'

const REEL2BITS_LICENSES = '/api/reel2bits/licenses'
const REEL2BITS_ALBUMS = (username) => `/api/albums/${username}`
const CHANGE_PASSWORD_URL = '/api/reel2bits/change_password'

const oldfetch = window.fetch

let fetch = (url, options) => {
  options = options || {}
  const baseUrl = ''
  const fullUrl = baseUrl + url
  options.credentials = 'same-origin'
  return oldfetch(fullUrl, options)
}

const authHeaders = (accessToken) => {
  if (accessToken) {
    return { 'Authorization': `Bearer ${accessToken}` }
  } else {
    return {}
  }
}

const promisedRequest = ({ method, url, payload, credentials, headers = {} }, store) => {
  const options = {
    method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...headers
    }
  }
  if (payload) {
    options.body = JSON.stringify(payload)
  }
  if (credentials) {
    options.headers = {
      ...options.headers,
      ...authHeaders(credentials)
    }
  }
  return fetch(url, options)
    .then((response) => {
      return new Promise((resolve, reject) => response.json()
        .then((json) => {
          if (!response.ok) {
            return reject(new StatusCodeError(response.status, json, { url, options }, response))
          }
          return resolve(json)
        }))
    })
}

/*
 * Parameters needed:
 *  nickname, email, fullname, password, password_confirm
 * Optionals:
 *  bio, homepage, location, token
 */
const register = (userInfo, store) => {
  console.debug('api.service::register', userInfo)
  const { nickname, ...rest } = userInfo
  return fetch(MASTODON_REGISTRATION_URL, {
    method: 'POST',
    headers: {
      ...authHeaders(store.getters.getToken()),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      nickname,
      locale: 'en_US',
      agreement: true,
      ...rest
    })
  })
    .then((response) => [response.ok, response])
    .then(([ok, response]) => {
      if (ok) {
        return response.json()
      } else {
        return response.json().then((error) => { throw new Error(error.error) })
      }
    })
}

const verifyCredentials = (user, store) => {
  return fetch(MASTODON_LOGIN_URL, {
    headers: authHeaders(user)
  })
    .then((response) => {
      if (response.ok) {
        return response.json()
      } else {
        return {
          error: response
        }
      }
    })
    .then((data) => data.error ? data : parseUser(data))
}

const trackUpload = (trackInfo, store) => {
  const form = new window.FormData()
  form.append('title', trackInfo.title)
  form.append('description', trackInfo.description)
  form.append('album', trackInfo.album)
  form.append('licence', trackInfo.licence)
  form.append('private', trackInfo.private)
  form.append('file', trackInfo.file)

  return fetch(TRACKS_UPLOAD_URL, {
    body: form,
    method: 'POST',
    headers: authHeaders(store.getters.getToken())
  })
    .then((response) => [response.ok, response])
    .then(([ok, response]) => {
      if (ok) {
        return response.json()
      } else {
        return response.json().then((error) => { throw new Error(error.error) })
      }
    })
}

const trackFetch = ({ user, trackId, credentials }) => {
  let url = TRACKS_FETCH_URL(user, trackId)

  return fetch(url, { headers: authHeaders(credentials) })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching track', data)
    })
    .then((data) => data.json())
    .then((data) => parseTrack(data))
}

const trackDelete = ({ user, trackId, credentials }) => {
  let url = TRACKS_DELETE_URL(user, trackId)

  return fetch(url, {
    headers: authHeaders(credentials),
    method: 'DELETE'
  })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error deleting track', data)
    })
    .then((data) => data.json())
}

const trackEdit = ({ username, trackId, track, credentials }) => {
  return promisedRequest({
    url: TRACKS_EDIT_URL(username, trackId),
    method: 'PATCH',
    payload: track,
    credentials: credentials
  }).then((data) => parseTrack(data))
}

const fetchUser = ({ id, store }) => {
  let url = `${MASTODON_USER_URL}/${id}`
  let credentials = store.getters.getToken()
  return promisedRequest({ url, credentials }, store)
    .then((data) => parseUser(data))
}

const updateUserSettings = ({ settings, credentials }) => {
  return promisedRequest({
    url: MASTODON_PROFILE_UPDATE_URL,
    method: 'PATCH',
    payload: settings,
    credentials: credentials
  }).then((data) => parseUser(data))
}

const fetchLicenses = () => {
  let url = REEL2BITS_LICENSES

  return fetch(url)
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching licenses', data)
    })
    .then((data) => data.json())
}

const fetchUserAlbums = ({ username, short = false, credentials }) => {
  let url = REEL2BITS_ALBUMS(username)

  const params = []
  params.push(['short', short])

  const queryString = map(params, (param) => `${param[0]}=${param[1]}`).join('&')
  url += `?${queryString}`

  return fetch(url, { headers: authHeaders(credentials) })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching albums', data)
    })
    .then((data) => data.json())
}

const albumNew = (albumInfo, store) => {
  const form = new window.FormData()
  form.append('title', albumInfo.title)
  form.append('description', albumInfo.description)
  form.append('private', albumInfo.private)

  return fetch(ALBUMS_NEW_URL, {
    body: form,
    method: 'POST',
    headers: authHeaders(store.getters.getToken())
  })
    .then((response) => [response.ok, response])
    .then(([ok, response]) => {
      if (ok) {
        return response.json()
      } else {
        return response.json().then((error) => { throw new Error(error.error) })
      }
    })
}

const albumFetch = (user, albumId, store) => {
  let url = ALBUMS_FETCH_URL(user, albumId)
  let credentials = store.getters.getToken()

  return fetch(url, { headers: authHeaders(credentials) })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching album', data)
    })
    .then((data) => data.json())
    .then((data) => parseAlbum(data))
}

const albumDelete = (user, trackId, store) => {
  let url = ALBUMS_DELETE_URL(user, trackId)
  let credentials = store.getters.getToken()

  return fetch(url, {
    headers: authHeaders(credentials),
    method: 'DELETE'
  })
}

const fetchUserLogs = (user, currentPage, perPage, store) => {
  let url = ACCOUNT_LOGS_URL(user, currentPage, perPage)
  let credentials = store.getters.getToken()

  return fetch(url, { headers: authHeaders(credentials) })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching user logs', data)
    })
    .then((data) => data.json())
}

const fetchTimeline = ({
  timeline,
  credentials,
  since = false,
  until = false,
  userId = false,
  tag = false,
  withMuted = false,
  page = 1
}) => {
  const timelineUrls = {
    public: MASTODON_PUBLIC_TIMELINE,
    friends: MASTODON_USER_HOME_TIMELINE_URL,
    dms: MASTODON_DIRECT_MESSAGES_TIMELINE_URL,
    notifications: MASTODON_USER_NOTIFICATIONS_URL,
    'publicAndExternal': MASTODON_PUBLIC_TIMELINE,
    user: MASTODON_USER_TIMELINE_URL
  }
  const params = []

  let url = timelineUrls[timeline]

  if (timeline === 'user' || timeline === 'media') {
    url = url(userId)
  }

  if (since) {
    params.push(['since_id', since])
  }
  if (until) {
    params.push(['max_id', until])
  }
  if (tag) {
    url = url(tag)
  }
  if (timeline === 'media') {
    params.push(['only_media', 1])
  }
  if (timeline === 'public') {
    params.push(['local', true])
  }
  if (timeline === 'public' || timeline === 'publicAndExternal') {
    params.push(['only_media', false])
  }
  if (page <= 0) {
    params.push(['page', 1])
  } else {
    params.push(['page', page])
  }

  params.push(['count', 5])
  params.push(['with_muted', withMuted])

  const queryString = map(params, (param) => `${param[0]}=${param[1]}`).join('&')
  url += `?${queryString}`

  return fetch(url, { headers: authHeaders(credentials) })
    .then((data) => {
      if (data.ok) {
        return data
      }
      throw new Error('Error fetching timeline', data)
    })
    .then((data) => data.json())
    .then((data) => {
      data.items = data.items.map(parseTrack)
      return data
    })
}

const changePassword = ({ credentials, password, newPassword, newPasswordConfirmation }) => {
  const form = new FormData()

  form.append('password', password)
  form.append('new_password', newPassword)
  form.append('new_password_confirmation', newPasswordConfirmation)

  return fetch(CHANGE_PASSWORD_URL, {
    body: form,
    method: 'POST',
    headers: authHeaders(credentials)
  })
    .then((response) => response.json())
}

const apiService = {
  verifyCredentials,
  register,
  fetchUser,
  trackUpload,
  trackDelete,
  trackEdit,
  trackFetch,
  albumNew,
  albumDelete,
  albumFetch,
  fetchUserLogs,
  fetchTimeline,
  fetchLicenses,
  fetchUserAlbums,
  updateUserSettings,
  changePassword
}

export default apiService
