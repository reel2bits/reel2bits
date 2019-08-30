<template>
  <Timeline
    title="Timeline"
    :timeline="timeline"
    :timeline-name="'friends'"
  />
</template>

<script>
import Timeline from '../timeline/timeline.vue'
const FriendsTimeline = {
  components: {
    Timeline
  },
  computed: {
    timeline () { return this.$store.state.statuses.timelines.friends }
  }
}

export default FriendsTimeline
</script>
