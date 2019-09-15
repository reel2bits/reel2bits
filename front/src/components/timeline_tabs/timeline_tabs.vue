<template>
  <b-nav tabs>
    <b-nav-item v-if="signedIn" :active="active == 'friends'" :to="{ name: 'friends' }">
      <translate translate-context="Content/TimelineTabs/Text/Tab">
        Your feed
      </translate>
    </b-nav-item>
    <b-nav-item :active="active == 'public'" :to="{ name: 'public-timeline' }">
      <translate translate-context="Content/TimelineTabs/Text/Tab">
        Public
      </translate>
    </b-nav-item>
    <b-nav-item :active="active == 'publicAndExternal'" :to="{ name: 'public-external-timeline' }">
      <translate translate-context="Content/TimelineTabs/Text/Tab">
        The Whole Known Network
      </translate>
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
