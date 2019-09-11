<template>
  <div id="app">
    <!-- Top navigation -->
    <nav class="navbar fixed-top bg-light">
      <div class="container">
        <div class="w-100 border-bottom align-items-center d-flex justify-content-between">
          <b-link :to="{ name: 'public-timeline' }" class="navbar-brand">
            <MainLogo :logo_spin_duration="logoSpinDuration" /><h3 class="text-body mx-3 d-inline">
              {{ sitename }}
            </h3>
          </b-link>
          <div class="col-md-4">
            <input id="topsearch" class="form-control" type="search"
                   :placeholder="labels.searchPlaceholder" :aria-label="labels.searchAria"
            >
          </div>
          <div>
            <span v-if="currentUser">

              <b-dropdown id="userDropdown" :button-content="labels.create"
                          right
                          variant="primary"
              >
                <b-dropdown-item>
                  <router-link :to="{ name: 'tracks-upload' }"
                               :button-content="labels.createTrack"
                  ><translate translate-context="Header/*/DropDown/Create/NewTrack text">New Track</translate></router-link>
                </b-dropdown-item>
                <b-dropdown-item>
                  <router-link :to="{ name: 'albums-new' }"
                               :button-content="labels.createAlbum"
                  ><translate translate-context="Header/*/DropDown/Create/NewAlbum text">New Album</translate></router-link>
                </b-dropdown-item>
              </b-dropdown>

              <router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">
                <img :src="currentUser.profile_image_url" class="rounded-circle mx-2" width="40"
                     height="40" :alt="usernameAvatar"
                     :title="labels.myAvatarTitle"
                >
              </router-link>
              <b-dropdown id="userDropdown" :button-content="atUsername"
                          right
                          variant="link"
                          toggle-class="px-0 text-decoration-none"
              >
                <b-dropdown-item><router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }"><translate translate-context="Header/*/DropDown/User/MyProfile">My Profile</translate></router-link></b-dropdown-item>
                <b-dropdown-item><router-link :to="{ name: 'user-settings' }"><translate translate-context="Header/*/DropDown/User/Settings">Settings</translate></router-link></b-dropdown-item>
                <b-dropdown-item><router-link :to="{ name: 'account-logs' }"><translate translate-context="Header/*/DropDown/User/Logs">Logs</translate></router-link></b-dropdown-item>
                <b-dropdown-divider />
                <b-dropdown-item><a href="#" @click.prevent="logout"><translate translate-context="Header/*/DropDown/User/Logout">Logout</translate></a></b-dropdown-item>
              </b-dropdown>
            </span>
            <span v-else>
              <b-button type="button" variant="link"
                        :to="{ name: 'login_form' }"
              ><translate translate-context="Header/*/DropDown/User/Login">Login</translate></b-button>
              <b-button v-if="registrationOpen"
                        type="button" variant="primary"
                        :to="{ name: 'register' }"
              ><translate translate-context="Header/*/DropDown/User/Register">Register</translate></b-button>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- content -->
    <div class="container">
      <transition name="fade">
        <router-view :key="$route.fullPath" @updateLogoSpinDuration="updateLogoSpinDuration" />
      </transition>
    </div>
  </div>
</template>

<style lang="scss" src="./App.scss"></style>

<script>
import Vue from 'vue'
import MainLogo from 'components/main_logo/main_logo.vue'
import { mapState } from 'vuex'
import locales from './locales.js'

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
    usernameAvatar () {
      let msg = this.$pgettext('Header/*/Image/Avatar alt', '%{username} avatar')
      return this.$gettextInterpolate(msg, { username: this.currentUser.screen_name })
    },
    labels () {
      return {
        searchPlaceholder: this.$pgettext('Header/*/Input/Search placeholder', 'Search'),
        searchAria: this.$pgettext('Header/*/Input/Search ARIA', 'Search'),
        create: this.$pgettext('Header/*/DropDown/Create', 'Create'),
        createTrack: this.$pgettext('Header/*/DropDown/Create/NewTrack title', 'new track'),
        createAlbum: this.$pgettext('Header/*/DropDown/Create/NewAlbum title', 'new album'),
        myAvatarTitle: this.$pgettext('Header/*/Image/Avatar title', 'go to my profile')
      }
    }
  },
  watch: {
    '$store.state.config.interfaceLanguage': {
      immediate: true,
      handler (newValue) {
        console.log('Switching interface language to', newValue)
        console.log('Available languages:', this.$language.available)
        import(`./translations/${newValue}.json`).then((response) => {
          Vue.$translations[newValue] = response.default[newValue]
        }).finally(() => {
          // set current language twice, otherwise we seem to have a cache somewhere
          // and rendering does not happen
          this.$language.current = 'noop'
          this.$language.current = newValue
          console.log('Interface set to', newValue)
        })
        if (newValue === 'en_us') {
          return this.$store.dispatch('setOption', { name: 'momentLocale', value: 'en' })
        }
        let momentLocale = newValue.replace('_', '-').toLowerCase()
        import(`moment/locale/${momentLocale}.js`).then(() => {
          this.$store.dispatch('setOption', { name: 'momentLocale', value: momentLocale })
        }).catch(() => {
          console.log('No momentjs locale available for', momentLocale)
          let shortLocale = momentLocale.split('-')[0]
          import(`moment/locale/${shortLocale}.js`).then(() => {
            this.$store.dispatch('setOption', { name: 'momentLocale', value: shortLocale })
          }).catch(() => {
            console.log('No momentjs locale available for short', shortLocale)
          })
        })
      }
    }
  },
  created () {
    this.autodetectLanguage()
  },
  methods: {
    logout () {
      this.$router.replace('/main/public')
      this.$store.dispatch('logout')
    },
    updateLogoSpinDuration (dur) {
      this.logoSpinDuration = dur
    },
    autodetectLanguage () {
      let userLanguage = navigator.language || navigator.userLanguage
      let available = locales.locales.map(e => { return e.code })
      let candidate
      let matching = available.filter((a) => {
        return userLanguage.replace('-', '_') === a
      })
      let almostMatching = available.filter((a) => {
        return userLanguage.replace('-', '_').split('_')[0] === a.split('_')[0]
      })
      if (matching.length > 0) {
        candidate = matching[0]
      } else if (almostMatching.length > 0) {
        candidate = almostMatching[0]
      } else {
        return
      }
      this.$store.dispatch('setOption', { name: 'interfaceLanguage', value: candidate })
    }
  }
}
</script>
