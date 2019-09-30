<template>
  <div class="row">
    <div class="col-md-8">
      <TimelineTabs active="friends" />

      <Timeline
        timeline-name="friends"
      />
    </div>
    <div class="col-md-4">
      <Sidebar />
    </div>
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
import Sidebar from '../sidebar/sidebar.vue'
const FriendsTimeline = {
  components: {
    TimelineTabs,
    Timeline,
    Sidebar
  }
}

export default FriendsTimeline
</script>
