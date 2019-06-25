<template>
  <div class="about">
    <h1>Profile page of {{currentUser.screen_name}}</h1>
  </div>
</template>

<script>
export default {
  computed: {
    currentUser () { return this.$store.state.users.currentUser }
  },
  created: function () {
    let user = !!this.$store.state.users.currentUser
    if (!user) {
      this.$router.push({ name: 'home' })
    }
  }
}
</script>
