<template>
  <div class="about">
    <h1>Profile page of {{currentUser.screen_name}}</h1>
  </div>
</template>

<script>
export default {
  computed: {
    currentUser () { return this.$store.state.users.currentUser }
  }
}
</script>
