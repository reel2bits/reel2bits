import axios from 'axios'

const MASTODON_LOGIN_URL = '/api/v1/accounts/verify_credentials'
const MASTODON_REGISTRATION_URL = '/api/v1/accounts'
const MASTODON_USER_URL = '/api/v1/accounts'

const apiClient = axios.create({
  // baseURL: store.state.instance.instanceUrl,
})

const authHeaders = (accessToken) => {
  if (accessToken) {
    return { 'Authorization': `Bearer ${accessToken}` }
  } else {
    return {}
  }
}

const headers = (accessToken=null) => {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...authHeaders(accessToken)
  }
}

/*
 * Parameters needed:
 *  nickname, email, fullname, password, password_confirm
 * Optionals:
 *  bio, homepage, location, token
 */
const register = (params) => {
  const { nickname, ...rest } = params

  const body = JSON.stringify({
    nickname,
    locale: 'en_US',
    agreement: true,
    ...rest
  })

  return apiClient.post(MASTODON_REGISTRATION_URL,
    body,
    { headers: headers() })
    .then((response) => [response.ok, response])
    .then(([ok, response]) => {
      if (ok) {
        return response.data
      } else {
        return response.data.then((error) => { throw new Error(error) })
      }
    })
}

const apiService = {
  apiClient,
  headers,
  authHeaders,
  register
}

export default apiService
