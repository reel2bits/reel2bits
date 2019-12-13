<template>
  <div id="app">
    <!-- Top navigation -->
    <b-navbar toggleable="lg" class="fixed-top bg-light">
      <div class="container">
        <div class="w-100 border-bottom align-items-center d-flex">
          <b-navbar-toggle target="nav-collapse" />
          <b-navbar-brand :to="{ name: 'public-timeline' }" class="d-flex mr-auto align-items-center w-50">
            <MainLogo :logo_spin_duration="logoSpinDuration" />
            <h3 class="text-body mx-3">
              {{ sitename }}
            </h3>
          </b-navbar-brand>
          <b-collapse id="nav-collapse" is-nav class="w-100">
            <div class="w-100 justify-content-center">
              <input id="topsearch" class="form-control" type="search"
                     :placeholder="labels.searchPlaceholder" :aria-label="labels.searchAria"
              >
            </div>
            <div class="ml-auto w-100 justify-content-end text-right">
              <span v-if="currentUser">
                <b-dropdown id="userDropdown" :text="labels.create"
                            right
                            variant="primary"
                            toggle-class="mx-2"
                >
                  <b-dropdown-item>
                    <router-link :to="{ name: 'tracks-upload' }"
                                 :text="labels.createTrack"
                    ><translate translate-context="Header/*/DropDown/Create/NewTrack text">New Track</translate></router-link>
                  </b-dropdown-item>
                  <b-dropdown-item>
                    <router-link :to="{ name: 'albums-new' }"
                                 :text="labels.createAlbum"
                    ><translate translate-context="Header/*/DropDown/Create/NewAlbum text">New Album</translate></router-link>
                  </b-dropdown-item>
                </b-dropdown>

                <router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">
                  <img :src="currentUser.profile_image_url" class="rounded-circle mx-2" width="40"
                       height="40" :alt="usernameAvatar"
                       :title="labels.myAvatarTitle"
                  >
                </router-link>
                <b-dropdown id="userDropdown" :text="atUsername"
                            right
                            variant="link"
                            toggle-class="px-0 text-decoration-none text-body mr-3"
                >
                  <b-dropdown-item><router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }"><translate translate-context="Header/*/DropDown/User/MyProfile">My Profile</translate></router-link></b-dropdown-item>
                  <b-dropdown-item><router-link :to="{ name: 'user-settings' }"><translate translate-context="Header/*/DropDown/User/Settings">Settings</translate></router-link></b-dropdown-item>
                  <b-dropdown-item><router-link :to="{ name: 'account-logs' }"><translate translate-context="Header/*/DropDown/User/Logs">Logs</translate></router-link></b-dropdown-item>
                  <b-dropdown-item><router-link :to="{ name: 'account-quota' }"><translate translate-context="Header/*/DropDown/User/Quota">Quota</translate></router-link></b-dropdown-item>
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
          </b-collapse>
        </div>
      </div>
    </b-navbar>

    <!-- content -->
    <div class="container">
      <b-alert v-if="severeBackendError" variant="danger" show>
        <i class="fa fa-warning" />
        <translate translate-context="*/*/Content/Alert">
          The backend cannot be reached properly, some functions might not work.
        </translate>
      </b-alert>

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
      const msg = this.$pgettext('Header/*/Image/Avatar alt', '%{username} avatar')
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
    },
    severeBackendError () {
      if (!this.$store.state.instance.backendVersion) {
        return true
      }
      return false
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
        const momentLocale = newValue.replace('_', '-').toLowerCase()
        import(`moment/locale/${momentLocale}.js`).then(() => {
          this.$store.dispatch('setOption', { name: 'momentLocale', value: momentLocale })
        }).catch(() => {
          console.log('No momentjs locale available for', momentLocale)
          const shortLocale = momentLocale.split('-')[0]
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
      if (this.currentUser) {
        console.log('logged in user, overriding language with account setting:', this.currentUser.reel2bits.lang)
        this.$store.dispatch('setOption', { name: 'interfaceLanguage', value: this.currentUser.reel2bits.lang })
        return
      }
      console.log('user not logged in, detecting language...')
      const userLanguage = navigator.language || navigator.userLanguage
      const available = locales.locales.map(e => { return e.code })
      let candidate
      const matching = available.filter((a) => {
        return userLanguage.replace('-', '_') === a
      })
      const almostMatching = available.filter((a) => {
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
