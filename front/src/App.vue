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
            <b-button-group>
              <b-button type="button" variant="light"
                        :to="{ name: 'public-external-timeline' }"
                        text="The Whole Known Network"
              >
                TWKN
              </b-button>
              <b-button type="button" variant="light"
                        :to="{ name: 'public-timeline' }"
                        text="Public"
              >
                PUB
              </b-button>
            </b-button-group>

            <span v-if="currentUser">
              <b-button-group>
                <b-button type="button" variant="primary"
                          :to="{ name: 'tracks-upload' }"
                          text="new track"
                >track</b-button>
                <b-button type="button" variant="info"
                          :to="{ name: 'albums-new' }"
                          text="new album"
                >album</b-button>
              </b-button-group>
              <router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">
                <img :src="currentUser.profile_image_url" class="rounded-circle mx-2" width="40"
                     height="40" :alt="usernameAvatar"
                     title="go to profile"
                >
              </router-link>
              <b-dropdown id="userDropdown" :text="atUsername" class="m-md-2">
                <b-dropdown-item><router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">My profile</router-link></b-dropdown-item>
                <b-dropdown-item><router-link :to="{ name: 'user-settings' }">Settings</router-link></b-dropdown-item>
                <b-dropdown-item><router-link :to="{ name: 'account-logs' }">Logs</router-link></b-dropdown-item>
                <b-dropdown-divider />
                <b-dropdown-item><a href="#" @click.prevent="logout">Logout</a></b-dropdown-item>
              </b-dropdown>
            </span>
            <span v-else>
              <b-button-group>
                <b-button type="button" variant="primary"
                          :to="{ name: 'login_form' }"
                >Login</b-button>
                <b-button v-if="registrationOpen"
                          type="button" variant="info"
                          :to="{ name: 'register' }"
                >Register</b-button>
              </b-button-group>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- content -->
    <div class="container">
      <transition name="fade">
        <router-view @updateLogoSpinDuration="updateLogoSpinDuration" />
      </transition>
    </div>
  </div>
</template>

<style lang="scss" src="./App.scss"></style>

<script>
import MainLogo from 'components/main_logo/main_logo.vue'
import { mapState } from 'vuex'

export default {
  name: 'App',
  components: {
    MainLogo
  },
  data: () => ({
    logoSpinDuration: false
  }),
  computed: {
    ...mapState({
      registrationOpen: state => state.instance.registrationOpen
    }),
    currentUser () { return this.$store.state.users.currentUser },
    sitename () { return this.$store.state.instance.name },
    atUsername () { return '@' + this.currentUser.screen_name },
    usernameAvatar () { return this.currentUser.screen_name + ' avatar' }
  },
  methods: {
    logout () {
      this.$router.replace('/main/public')
      this.$store.dispatch('logout')
    },
    updateLogoSpinDuration (dur) {
      this.logoSpinDuration = dur
    }
  }
}
</script>
