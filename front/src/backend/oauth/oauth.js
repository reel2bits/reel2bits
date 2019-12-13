// Snippets extracted from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/new_api/oauth.js
import { reduce } from 'lodash'

const REDIRECT_URI = `${window.location.origin}/oauth-callback`

export const getOrCreateApp = ({ clientId, clientSecret, commit }) => {
  console.debug('getOrCreateApp')
  if (clientId && clientSecret) {
    console.debug('we already have clientId and clientSecret stored')
    return Promise.resolve({ clientId, clientSecret })
  }
  console.debug('registering a new app')

  const url = '/api/v1/apps'
  const form = new window.FormData()

  form.append('client_name', `reel2bit_front_${window.___reel2bitsfe_commit_hash}_${(new Date()).toISOString()}`)
  form.append('redirect_uris', REDIRECT_URI)
  form.append('scopes', 'read write follow push')

  return window.fetch(url, {
    method: 'POST',
    body: form
  })
    .then((data) => data.json())
    .then((app) => ({ clientId: app.client_id, clientSecret: app.client_secret }))
    .then((app) => commit('setClientData', app) || app)
}

const login = ({ clientId }) => {
  console.debug('login')
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
  window.location.href = `/oauth/authorize?${dataString}`
}

// Used on : login
const getTokenWithCredentials = ({ clientId, clientSecret, username, password }) => {
  console.debug('getTokenWithCredentials')
  const url = '/oauth/token'
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'password')
  form.append('scope', 'read write follow push')
  form.append('username', username)
  form.append('password', password)

  return window.fetch(url, {
    method: 'POST',
    body: form
  }).then((data) => data.json())
}

const getToken = ({ clientId, clientSecret, code }) => {
  console.debug('getToken')
  const url = '/oauth/token'
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'authorization_code')
  form.append('code', code)
  form.append('token_endpoint_auth_method', 'client_secret_post')
  form.append('scope', 'read write follow push')
  form.append('redirect_uri', `${window.location.origin}/oauth-callback`)

  return window.fetch(url, {
    method: 'POST',
    body: form
  }).then((data) => data.json())
}

export const getClientToken = ({ clientId, clientSecret }) => {
  console.debug('getClientToken')
  const url = '/oauth/token'
  const form = new window.FormData()

  form.append('client_id', clientId)
  form.append('client_secret', clientSecret)
  form.append('grant_type', 'client_credentials')
  form.append('scope', 'read write follow push')
  form.append('redirect_uri', `${window.location.origin}/oauth-callback`)

  return window.fetch(url, {
    method: 'POST',
    body: form
  }).then((data) => data.json())
}

const revokeToken = ({ app, token }) => {
  const url = '/oauth/revoke'
  const form = new window.FormData()

  form.append('client_id', app.clientId)
  form.append('client_secret', app.clientSecret)
  form.append('token', token)

  const auth = window.btoa(token)

  return window.fetch(url, {
    headers: { Authorization: `Basic ${auth}` },
    method: 'POST',
    body: form
  }).then((data) => data.json())
}

const oauth = {
  login,
  getToken,
  getTokenWithCredentials,
  getOrCreateApp,
  revokeToken
}

export default oauth
