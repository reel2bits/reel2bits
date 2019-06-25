import axios from 'axios'
import { parseUser } from '../entity_normalizer/entity_normalizer.service.js'
import { StatusCodeError } from '../errors/errors'

const MASTODON_LOGIN_URL = '/api/v1/accounts/verify_credentials'
const MASTODON_REGISTRATION_URL = '/api/v1/accounts'
const MASTODON_USER_URL = '/api/v1/accounts'

const apiClient = axios.create({
  // baseURL: this.$store.state.instance.instanceUrl
})

const authHeaders = (accessToken) => {
  if (accessToken) {
    return { 'Authorization': `Bearer ${accessToken}` }
  } else {
    return {}
  }
}

const headers = (accessToken = null) => {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...authHeaders(accessToken)
  }
}

/* Dirty thing used in after_store.js:setSettings to set the baseURL of the
 * apiClient after initialization
 * It can probably done better...
 * FIXME
 */
const setBaseUrl = (baseUrl) => {
  apiClient.defaults.baseURL = baseUrl
}

const promisedRequest = ({ method = 'get', url, payload, credentials }) => {
  const body = payload ? JSON.stringify(payload) : null
  const hdrs = headers(credentials)
  if (method === 'get') {
    return apiClient.get(url, { headers: hdrs })
      .then(response => {
        return response.data
      })
      .catch(response => {
        return new StatusCodeError(response.status, response.data, { url, hdrs }, response)
      })
  } else if (method === 'post') {
    return apiClient.post(url, body, { headers: hdrs })
      .then(response => {
        return response.data
      })
      .catch(response => {
        return new StatusCodeError(response.status, response.data, { url, hdrs }, response)
      })
  }
}

/*
 * Parameters needed:
 *  nickname, email, fullname, password, password_confirm
 * Optionals:
 *  bio, homepage, location, token
 */
const register = (params, store) => {
  const { nickname, ...rest } = params

  const body = JSON.stringify({
    nickname,
    locale: 'en_US',
    agreement: true,
    ...rest
  })

  return apiClient.post(MASTODON_REGISTRATION_URL,
    body,
    { headers: headers(store.getters.getToken()) })
    .then(response => {
      return response.data
    })
    .catch(error => {
      throw new Error(error)
    })
}

const verifyCredentials = (user, store) => {
  return apiClient.post(MASTODON_LOGIN_URL, null, { headers: headers(store.getters.getToken()) })
    .then(response => {
      return parseUser(response.data)
    })
    .catch(response => {
      return { error: response }
    })
}

const fetchUser = ({ id, credentials }) => {
  let url = `${MASTODON_USER_URL}/${id}`
  return promisedRequest({ url, credentials })
    .then((data) => parseUser(data))
}

const apiService = {
  verifyCredentials,
  apiClient,
  headers,
  authHeaders,
  register,
  setBaseUrl,
  fetchUser
}

export default apiService
