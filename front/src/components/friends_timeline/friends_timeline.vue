<template>
  <div>
    <TimelineTabs active="friends" />

    <Timeline
      title="Timeline"
      timeline-name="friends"
    />
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
const FriendsTimeline = {
  components: {
    TimelineTabs,
    Timeline
  }
}

export default FriendsTimeline
</script>
