<template>
  <div class="row">
    <div class="col-md-8">
      <TimelineTabs active="publicAndExternal" />

      <Timeline
        title="The Whole Known Network"
        :timeline-name="'publicAndExternal'"
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
const PublicAndExternalTimeline = {
  components: {
    TimelineTabs,
    Timeline,
    Footer
  }
}

export default PublicAndExternalTimeline
</script>
