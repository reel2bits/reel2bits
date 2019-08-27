<template>
  <div class="home">
    home blah blah blah
  </div>
</template>

<script>
// @ is an alias to /src

// TODO: this will be reworked, this shouldn't be friends timeline
export default {
  created () {
    this.$store.dispatch('startFetchingTimeline', { timeline: 'friends' })
  },
  destroyed () {
    this.$store.dispatch('stopFetching', 'friends')
  }
}
</script>
