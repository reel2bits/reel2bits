<template>
  <b-nav tabs>
    <b-nav-item :active="active == 'friends'" :to="{ name: 'friends' }">
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
const TimelineTabs = {
  props: [
    'active'
  ]
}

export default TimelineTabs
</script>
