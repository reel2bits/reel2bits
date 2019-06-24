import axios from 'axios'

// const MASTODON_LOGIN_URL = '/api/v1/accounts/verify_credentials'
const MASTODON_REGISTRATION_URL = '/api/v1/accounts'
// const MASTODON_USER_URL = '/api/v1/accounts'

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

const apiService = {
  apiClient,
  headers,
  authHeaders,
  register,
  setBaseUrl
}

export default apiService
