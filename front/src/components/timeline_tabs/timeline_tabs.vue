<template>
  <b-nav tabs>
    <b-nav-item v-if="signedIn" :active="active == 'friends'" :to="{ name: 'friends' }">
      Your feed
    </b-nav-item>
    <b-nav-item :active="active == 'public'" :to="{ name: 'public-timeline' }">
      Public
    </b-nav-item>
    <b-nav-item :active="active == 'publicAndExternal'" :to="{ name: 'public-external-timeline' }">
      The Whole Known Network
    </b-nav-item>
  </b-nav>
</template>

<script>
import { mapState } from 'vuex'

const TimelineTabs = {
  props: [
    'active'
  ],
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    })
  }
}

export default TimelineTabs
</script>
