<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        Track: {{ track.reel2bits.title }}<br>
        Published on: {{ track.created_at }}
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
