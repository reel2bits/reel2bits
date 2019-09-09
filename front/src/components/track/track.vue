<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        Track: <b-link :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }">
          {{ track.title }}
        </b-link><br>
        Published on: {{ track.uploaded_on }}
        <hr>
      </div>
    </div>
  </div>
</template>

<script>
const Track = {
  props: [
    'track'
  ]
}

export default Track
</script>
