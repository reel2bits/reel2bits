// Imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/user_profile_link_generator/user_profile_link_generator.js

import { includes } from 'lodash'

const generateRemoteLink = (id, screenName, restrictedNicknames, suffix, trackId = null) => {
  const complicated = !screenName || (isExternal(screenName) || includes(restrictedNicknames, screenName))
  if (trackId) {
    return {
      name: (complicated ? `external-${suffix}` : suffix),
      params: (complicated ? { id: id, trackId: trackId } : { username: screenName, trackId: trackId })
    }
  } else {
    return {
      name: (complicated ? `external-${suffix}` : suffix),
      params: (complicated ? { id: id } : { name: screenName })
    }
  }
}

const isExternal = screenName => screenName && screenName.includes('@')

export default generateRemoteLink
