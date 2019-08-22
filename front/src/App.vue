<template>
  <div id="app">
    <!-- Top navigation -->
    <nav class="navbar fixed-top bg-light">
      <div class="container">
        <div class="w-100 border-bottom align-items-center d-flex justify-content-between">
          <b-link to="/" class="navbar-brand">
            <img src="/static/logo.svg" width="64" height="64"
                 alt="Reel2Bits logo"
            ><h3 class="text-body mx-3 d-inline">
              {{ sitename }}
            </h3>
          </b-link>
          <div class="col-md-4">
            <input id="topsearch" class="form-control" type="search"
                   placeholder="Search" aria-label="Search"
            >
          </div>
          <div>
            <router-link to="/about">
              About
            </router-link>
            <span v-if="currentUser">
              | <router-link to="/tracks/upload">Upload track</router-link>
              | <router-link to="/albums/new">New album</router-link>
              | <router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">Me</router-link>
              | <a
                href="#"
                @click.prevent="logout"
              >Logout</a></span>
            <span v-else>
              | <router-link to="/login">Login</router-link>
              |
              <router-link
                v-if="!currentUser"
                to="/register"
              >Register</router-link>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- content -->
    <div class="container">
      <router-view />
    </div>
  </div>
</template>

<style lang="scss" src="./App.scss"></style>

<script>
export default {
  name: 'App',
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
