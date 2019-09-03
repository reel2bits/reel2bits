<template>
  <div>
    <TimelineTabs active="public" />

    <Timeline
      title="Public Timeline"
      timeline-name="public"
    />
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
const PublicTimeline = {
  components: {
    TimelineTabs,
    Timeline
  }
}

export default PublicTimeline
</script>
