<template>
  <div id="app">
    <!-- Top navigation -->
    <nav class="navbar fixed-top bg-light">
      <div class="container">
        <div class="w-100 border-bottom align-items-center d-flex justify-content-between">
          <b-link to="/" class="navbar-brand">
            <MainLogo :logo_spin_duration="logoSpinDuration" /><h3 class="text-body mx-3 d-inline">
              {{ sitename }}
            </h3>
          </b-link>
          <div class="col-md-4">
            <input id="topsearch" class="form-control" type="search"
                   placeholder="Search" aria-label="Search"
            >
          </div>
          <div>
            <span v-if="currentUser">
              <router-link to="/tracks/upload">Upload track</router-link>
              | <router-link to="/albums/new">New album</router-link>
              | <router-link to="/account/logs">logs</router-link>
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
      <router-view @updateLogoSpinDuration="updateLogoSpinDuration" />
    </div>
  </div>
</template>

<style lang="scss" src="./App.scss"></style>

<script>
import MainLogo from 'components/main_logo/main_logo.vue'

export default {
  name: 'App',
  components: {
    MainLogo
  },
  data: () => ({
    logoSpinDuration: '0s'
  }),
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    sitename () { return this.$store.state.instance.name }
  },
  methods: {
    logout () {
      this.$router.replace('/')
      this.$store.dispatch('logout')
    },
    updateLogoSpinDuration (dur) {
      this.logoSpinDuration = dur
    }
  }
}
</script>
