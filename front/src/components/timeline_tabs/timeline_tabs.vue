<template>
  <b-nav class="mb-4">
    <b-nav-item v-if="signedIn" :active="active == 'friends'" :to="{ name: 'friends' }"
                class="border-right pr-3"
    >
      <translate translate-context="Content/TimelineTabs/Text/Tab">
        Your feed
      </translate>
    </b-nav-item>
    <b-nav-item :active="active == 'public'" :to="{ name: 'public-timeline' }"
                class="border-right px-3"
    >
      <translate translate-context="Content/TimelineTabs/Text/Tab">
        Public
      </translate>
    </b-nav-item>
    <b-nav-item :active="active == 'publicAndExternal'" :to="{ name: 'public-external-timeline' }"
                class="px-3"
    >
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
