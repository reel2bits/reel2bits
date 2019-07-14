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
    output.profile_image_url = data.avatar
    output.profile_image_url_original = data.avatar

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

  output.tags = output.tags || []
  output.rights = output.rights || {}
  output.notification_settings = output.notification_settings || {}

  return output
}

export const parseTrack = (data) => {
  const output = {}

  output.id = String(data.id)
  output.title = data.title
  output.user = data.user
  output.description = data.description
  output.picture_url = data.picture_url
  output.media_orig = data.media_orig
  output.media_transcoded = data.media_transcoded
  output.waveform = data.waveform
  output.private = data.private
  output.uploaded_on = data.uploaded_on
  output.uploaded_elapsed = data.uploaded_elapsed
  output.album_id = data.album_id

  output.processing = {}
  output.processing.basic = data.processing.basic
  output.processing.transcode_state = data.processing.transcode_state
  output.processing.transcode_needed = data.processing.transcode_needed
  output.processing.done = data.processing.done

  output.metadatas = {}
  output.metadatas.licence = data.metadatas.licence
  output.metadatas.duration = data.metadatas.duration
  output.metadatas.type = data.metadatas.type
  output.metadatas.codec = data.metadatas.codec
  output.metadatas.format = data.metadatas.format
  output.metadatas.channels = data.metadatas.channels
  output.metadatas.rate = data.metadatas.rate
  output.metadatas.bitrate = data.metadatas.bitrate
  output.metadatas.bitrate_mode = data.metadatas.bitrate_mode

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
  output.sounds = data.sounds
  output.flake_id = data.flake_id
  output.timeline = data.timeline

  return output
}
