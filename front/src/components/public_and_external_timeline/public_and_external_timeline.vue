<template>
  <Timeline
    title="The Whole Known Network"
    :timeline-name="'publicAndExternal'"
  />
</template>

<script>
import Timeline from '../timeline/timeline.vue'
const PublicAndExternalTimeline = {
  components: {
    Timeline
  }
}

export default PublicAndExternalTimeline
</script>
