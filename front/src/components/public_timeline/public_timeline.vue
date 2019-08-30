<template>
  <Timeline
    title="Public Timeline"
    :timeline="timeline"
    :timeline-name="'public'"
  />
</template>

<script>
import Timeline from '../timeline/timeline.vue'
const PublicTimeline = {
  components: {
    Timeline
  },
  computed: {
    timeline () { return this.$store.state.statuses.timelines.public }
  },
  created () {
    this.$store.dispatch('startFetchingTimeline', { timeline: 'public' })
  },
  destroyed () {
    this.$store.dispatch('stopFetching', 'public')
  }

}

export default PublicTimeline
</script>
