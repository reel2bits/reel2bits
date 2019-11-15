// Imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/user_profile_link_generator/user_profile_link_generator.js

import { includes } from 'lodash'

const generateRemoteLink = (id, screenName, restrictedNicknames, suffix) => {
  const complicated = !screenName || (isExternal(screenName) || includes(restrictedNicknames, screenName))
  return {
    name: (complicated ? `external-${suffix}` : suffix),
    params: (complicated ? { id } : { name: screenName })
  }
}

const isExternal = screenName => screenName && screenName.includes('@')

export default generateRemoteLink
