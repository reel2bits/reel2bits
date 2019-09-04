// addEmojis and parseUser are from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/services/entity_normalizer/entity_normalizer.service.js

export const addEmojis = (string, emojis) => {
  return emojis.reduce((acc, emoji) => {
    return acc.replace(
      new RegExp(`:${emoji.shortcode}:`, 'g'),
      `<img src='${emoji.url}' alt='${emoji.shortcode}' title='${emoji.shortcode}' class='emoji' />`
    )
  }, string)
}

export const parseUser = (data) => {
  const output = {}
  const masto = data.hasOwnProperty('acct')
  // case for users in "mentions" property for statuses in MastoAPI
  const mastoShort = masto && !data.hasOwnProperty('avatar')

  output.id = String(data.id)

  if (masto) {
    output.screen_name = data.acct
    output.statusnet_profile_url = data.url

    // There's nothing else to get
    if (mastoShort) {
      return output
    }

    output.name = data.display_name
    output.name_html = addEmojis(data.display_name, data.emojis)

    output.description = data.note
    output.description_html = addEmojis(data.note, data.emojis)

    // Utilize avatar_static for gif avatars?
    output.profile_image_url = (data.avatar || '/static/userpic_placeholder.svg')
    output.profile_image_url_original = (data.avatar || '/static/userpic_placeholder.svg')

    // Same, utilize header_static?
    output.cover_photo = data.header

    output.friends_count = data.following_count

    output.bot = data.bot

    if (data.source) {
      output.description = data.source.note
      output.default_scope = data.source.privacy
    }

    // TODO: handle is_local
    output.is_local = !output.screen_name.includes('@')
  } else {
    output.screen_name = data.screen_name

    output.name = data.name
    output.name_html = data.name_html

    output.description = data.description
    output.description_html = data.description_html

    output.profile_image_url = data.profile_image_url
    output.profile_image_url_original = data.profile_image_url_original

    output.cover_photo = data.cover_photo

    output.friends_count = data.friends_count

    // output.bot = ??? missing

    output.statusnet_profile_url = data.statusnet_profile_url

    output.statusnet_blocking = data.statusnet_blocking

    output.is_local = data.is_local
    output.role = data.role
    output.show_role = data.show_role

    output.follows_you = data.follows_you

    output.muted = data.muted

    if (data.rights) {
      output.rights = {
        moderator: data.rights.delete_others_notice,
        admin: data.rights.admin
      }
    }
    output.no_rich_text = data.no_rich_text
    output.default_scope = data.default_scope
    output.hide_follows = data.hide_follows
    output.hide_followers = data.hide_followers
    output.background_image = data.background_image
    // on mastoapi this info is contained in a "relationship"
    output.following = data.following
    // Websocket token
    output.token = data.token
  }

  output.created_at = new Date(data.created_at)
  output.locked = data.locked
  output.followers_count = data.followers_count
  output.statuses_count = data.statuses_count
  output.friendIds = []
  output.followerIds = []
  output.pinnedStatuseIds = []
  output.albums_count = data.reel2bits.albums_count

  output.tags = output.tags || []
  output.rights = output.rights || {}
  output.notification_settings = output.notification_settings || {}

  if (data.reel2bits) {
    output.reel2bits = {}
    output.reel2bits.albums_count = data.reel2bits.albums_count
    output.reel2bits.lang = data.reel2bits.lang || 'en'
  }

  return output
}

export const parseTrack = (data) => {
  const output = {}

  output.id = String(data.id)
  output.title = data.reel2bits.title
  output.account = parseUser(data.account)
  output.description = data.content
  output.picture_url = (data.reel2bits.picture_url || '/static/artwork_placeholder.svg')
  output.media_orig = data.reel2bits.media_orig
  output.media_transcoded = data.reel2bits.media_transcoded
  output.waveform = data.reel2bits.waveform
  output.private = data.reel2bits.private
  output.uploaded_on = data.created_at
  output.uploaded_elapsed = data.uploaded_elapsed
  output.album_id = data.reel2bits.album_id
  output.favorited = data.favorited
  output.reblogged = data.reblogged
  output.comments = 0 // FIXME TODO

  output.type = (data.reel2bits.type || 'status')

  output.slug = data.reel2bits.slug

  if (output.type === 'track') {
    output.processing = {}
    output.processing.basic = data.reel2bits.processing.basic
    output.processing.transcode_state = data.reel2bits.processing.transcode_state
    output.processing.transcode_needed = data.reel2bits.processing.transcode_needed
    output.processing.done = data.reel2bits.processing.done

    output.metadatas = {}
    output.metadatas.licence = data.reel2bits.metadatas.licence
    output.metadatas.duration = data.reel2bits.metadatas.duration
    output.metadatas.type = data.reel2bits.metadatas.type
    output.metadatas.codec = data.reel2bits.metadatas.codec
    output.metadatas.format = data.reel2bits.metadatas.format
    output.metadatas.channels = data.reel2bits.metadatas.channels
    output.metadatas.rate = data.reel2bits.metadatas.rate
    output.metadatas.bitrate = data.reel2bits.metadatas.bitrate
    output.metadatas.bitrate_mode = data.reel2bits.metadatas.bitrate_mode
  }
  if (output.type === 'album') {
    output.tracks_count = data.reel2bits.tracks_count
  }
  return output
}

export const parseAlbum = (data) => {
  const output = {}

  output.id = String(data.id)
  output.title = data.title
  output.created = data.created
  output.updated = data.updated
  output.description = data.description
  output.private = data.private
  output.slug = data.slug
  output.user_id = data.user_id
  output.user = data.user
  output.sounds = data.sounds
  output.flake_id = data.flake_id
  output.timeline = data.timeline

  return output
}

export const parseNotification = (data) => {
  const mastoDict = {
    'favourite': 'like',
    'reblog': 'repeat'
  }
  const masto = !data.hasOwnProperty('ntype')
  const output = {}

  if (masto) {
    output.type = mastoDict[data.type] || data.type
    output.seen = data.pleroma.is_seen
    output.status = output.type === 'follow'
      ? null
      : parseTrack(data.status)
    output.action = output.status // TODO: Refactor, this is unneeded
    output.from_profile = parseUser(data.account)
  } else {
    const parsedNotice = parseTrack(data.notice)
    output.type = data.ntype
    output.seen = Boolean(data.is_seen)
    output.status = output.type === 'like'
      ? parseTrack(data.notice.favorited_status)
      : parsedNotice
    output.action = parsedNotice
    output.from_profile = parseUser(data.from_profile)
  }

  output.created_at = new Date(data.created_at)
  output.id = parseInt(data.id)

  return output
}
