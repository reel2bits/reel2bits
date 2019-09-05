<template>
  <div class="row">
    <div class="col-md-8">
      <TimelineTabs active="friends" />

      <Timeline
        title="Timeline"
        timeline-name="friends"
      />
    </div>
    <div class="col-md-4">
      <Footer />
    </div>
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
import Footer from '../footer/footer.vue'
const FriendsTimeline = {
  components: {
    TimelineTabs,
    Timeline,
    Footer
  }
}

export default FriendsTimeline
</script>
