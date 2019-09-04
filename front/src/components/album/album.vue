<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        Album: <b-link :to="{ name: 'albums-show', params: { username: album.account.screen_name, albumId: album.slug } }">
          {{ album.title }}
        </b-link><br>
        Tracks: {{ album.tracks_count }}<br>
        Published on: {{ album.uploaded_on }}
        <hr>
      </div>
    </div>
  </div>
</template>

<script>
const Album = {
  props: [
    'album'
  ]
}

export default Album
</script>
