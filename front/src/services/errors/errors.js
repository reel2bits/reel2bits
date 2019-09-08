// File imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/errors/errors.js
import { humanizeErrors } from '../../modules/errors'

export function StatusCodeError (statusCode, body, options, response) {
  this.name = 'StatusCodeError'
  this.statusCode = statusCode
  this.message = statusCode + ' - ' + (JSON && JSON.stringify ? JSON.stringify(body) : body)
  this.error = body // legacy attribute
  this.options = options
  this.response = response

  if (Error.captureStackTrace) { // required for non-V8 environments
    Error.captureStackTrace(this)
  }
}
StatusCodeError.prototype = Object.create(Error.prototype)
StatusCodeError.prototype.constructor = StatusCodeError

export class RegistrationError extends Error {
  constructor (error) {
    super()
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this)
    }

    try {
      // the error is probably a JSON object with a single key, "errors", whose value is another JSON object containing the real errors
      if (typeof error === 'string') {
        error = JSON.parse(error)
        if (error.hasOwnProperty('error')) {
          error = JSON.parse(error.error)
        }
      }

      if (typeof error === 'object') {
        if (error.error) {
          error = JSON.parse(error.error) // error might be embedded here
        }
        // replace ap_id with username
        if (error.ap_id) {
          error.username = error.ap_id
          delete error.ap_id
        }
        this.message = humanizeErrors(error)
      } else {
        this.message = error
      }
    } catch (e) {
      // can't parse it, so just treat it like a string
      this.message = error
    }
  }
}
