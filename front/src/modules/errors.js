// File imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/modules/errors.js

import { capitalize } from 'lodash'

export function humanizeErrors (errors) {
  return Object.entries(errors).reduce((errs, [k, val]) => {
    let message = val.reduce((acc, message) => {
      let key = capitalize(k.replace(/_/g, ' '))
      return acc + [key, message].join(' ') + '. '
    }, '')
    return [...errs, message]
  }, [])
}
