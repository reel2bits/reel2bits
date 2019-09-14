import { has, capitalize } from 'lodash'

// File imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/errors/registration_error.js

function tryJSONParse (str) {
  try {
    return JSON.parse(str)
  } catch (_) {
    return str
  }
}

function humanizeErrors (errors) {
  return Object.entries(errors).reduce((errs, [k, val]) => {
    let message = val.reduce((acc, message) => {
      let key = capitalize(k.replace(/_/g, ' '))
      return acc + [key, message].join(' ') + '. '
    }, '')
    return [...errs, message]
  }, [])
}

export default class RegistrationError extends Error {
  constructor (error) {
    super()
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this)
    }

    error = tryJSONParse(error)

    // the error is probably a JSON object with a single key, "error", whose value is another JSON object containing the real errors
    if (has(error, 'error')) {
      error = tryJSONParse(error.error)
    }

    if (typeof error === 'object') {
      try {
        // replace ap_id with username
        if (error.ap_id) {
          error.username = error.ap_id
          delete error.ap_id
        }
        this.errors = humanizeErrors(error)
      } catch (e) {
        // can't parse it, so just treat it like a string
        this.errors = [JSON.stringify(error)]
      }
    } else {
      this.errors = [error]
    }

    this.name = 'RegistrationError'
    this.message = this.errors.join()
  }
}
