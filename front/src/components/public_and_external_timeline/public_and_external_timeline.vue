<template>
  <div class="row">
    <div class="col-md-8">
      <TimelineTabs active="publicAndExternal" />

      <Timeline
        :timeline-name="'publicAndExternal'"
      />
    </div>
    <div class="col-md-4">
      <UserCard v-if="currentUser" :user="currentUser" />
      <Footer />
    </div>
  </div>
</template>

<script>
import TimelineTabs from '../timeline_tabs/timeline_tabs.vue'
import Timeline from '../timeline/timeline.vue'
import UserCard from '../../components/user_card/user_card.vue'
import Footer from '../footer/footer.vue'
const PublicAndExternalTimeline = {
  components: {
    TimelineTabs,
    Timeline,
    UserCard,
    Footer
  },
  computed: {
    currentUser () { return this.$store.state.users.currentUser }
  }
}

export default PublicAndExternalTimeline
</script>
