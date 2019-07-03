import { parseUser } from '../entity_normalizer/entity_normalizer.service.js'
import { StatusCodeError } from '../errors/errors'

const MASTODON_LOGIN_URL = '/api/v1/accounts/verify_credentials'
const MASTODON_REGISTRATION_URL = '/api/v1/accounts'
const MASTODON_USER_URL = '/api/v1/accounts'

const TRACKS_UPLOAD_URL = '/api/tracks/upload'
// const TRACKS_GET = '/api/tracks/:id' // GET
// const TRACKS_EDIT = '/api/tracks/:id' // PATCH
// const TRACKS_DELETE = '/api/tracks/:id' // DELETE

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

const fetchUser = ({ id, store }) => {
  let url = `${MASTODON_USER_URL}/${id}`
  let credentials = store.getters.getToken()
  return promisedRequest({ url, credentials }, store)
    .then((data) => parseUser(data))
}

const apiService = {
  verifyCredentials,
  register,
  fetchUser,
  trackUpload
}

export default apiService
