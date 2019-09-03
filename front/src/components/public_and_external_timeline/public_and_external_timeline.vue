<template>
  <div>
    <TimelineTabs active="publicAndExternal" />

    <Timeline
      title="The Whole Known Network"
      :timeline-name="'publicAndExternal'"
    />
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
const PublicAndExternalTimeline = {
  components: {
    TimelineTabs,
    Timeline
  }
}

export default PublicAndExternalTimeline
</script>
