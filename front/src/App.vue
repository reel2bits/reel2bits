<template>
  <div id="app">
    <div id="nav">
      <h1>{{ sitename }}</h1>
      <hr>
      <router-link to="/">Home</router-link> |
      <router-link to="/about">About</router-link>
      <span v-if="currentUser">
         | <router-link to="/tracks/upload">Upload track</router-link>
         | <a href="#" @click.prevent="logout">Logout</a></span>
      <span v-else>
        | <router-link to="/login">Login</router-link>
        |
        <router-link v-if="!currentUser" to="/register">Register</router-link>
      </span>
    </div>
    <router-view/>
  </div>
</template>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
#nav {
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>

<script>
export default {
  name: 'app',
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    sitename () { return this.$store.state.instance.name }
  },
  methods: {
    logout () {
      this.$router.replace('/')
      this.$store.dispatch('logout')
    }
  }
}
</script>
