<template>
  <div class="row mt-4">
    <div class="col-md-8">
      <TimelineTabs active="public" />

      <Timeline
        timeline-name="public"
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
const PublicTimeline = {
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

export default PublicTimeline
</script>
