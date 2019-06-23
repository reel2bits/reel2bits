// Snippets extracted from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/new_api/oauth.js
import axios from 'axios'
import { reduce } from 'lodash'

const REDIRECT_URI = `${window.location.origin}/oauth-callback`

export const getOrCreateApp = ({ clientId, clientSecret, instance, commit }) => {
  if (clientId && clientSecret) {
    return Promise.resolve({ clientId, clientSecret })
  }

  const url = `${instance}/api/v1/apps`
  const form = new window.FormData()

  form.append('client_name', `reel2bit_front_${(new Date()).toISOString()}`)
  form.append('redirect_uris', REDIRECT_URI)
  form.append('scopes', 'read write follow push')

  return axios.post(url, form)
    .then((data) => data.data)
    .then((app) => ({ clientId: app.client_id, clientSecret: app.client_secret }))
    .then((app) => commit('setClientData', app) || app)
}

const login = ({ instance, clientId }) => {
  const data = {
    response_type: 'code',
    client_id: clientId,
    redirect_uri: REDIRECT_URI,
    scope: 'read write follow push'
  }

  const dataString = reduce(data, (acc, v, k) => {
    const encoded = `${k}=${encodeURIComponent(v)}`
    if (!acc) {
      return encoded
    } else {
      return `${acc}&${encoded}`
    }
  }, false)

  // Do the redirect
  window.location.href = `${instance}/oauth/authorize?${dataString}`
}

const getTokenWithCredentials = ({ clientId, clientSecret, instance, username, password }) => {
  const url = `${instance}/oauth/token`
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'password')
  form.append('username', username)
  form.append('password', password)

  return axios.post(url, form).then((data) => data.data)
}

const getToken = ({ clientId, clientSecret, instance, code }) => {
  const url = `${instance}/oauth/token`
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'authorization_code')
  form.append('code', code)
  form.append('token_endpoint_auth_method', 'client_secret_post')
  form.append('redirect_uri', `${window.location.origin}/oauth-callback`)

  return axios.post(url, form).then((data) => data.data)
}

export const getClientToken = ({ clientId, clientSecret, instance }) => {
  const url = `${instance}/oauth/token`
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'client_credentials')
  form.append('redirect_uri', `${window.location.origin}/oauth-callback`)

  return axios.post(url, form).then((data) => data.data)
}

const oauth = {
  login,
  getToken,
  getTokenWithCredentials,
  getOrCreateApp
}

export default oauth
