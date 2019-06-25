// File imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/errors/errors.js

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
