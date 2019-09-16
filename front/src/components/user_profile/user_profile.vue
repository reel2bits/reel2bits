<template>
  <div>
    <div v-if="error">
      {{ error }}
    </div>
    <div v-if="user">
      <div class="row mt-4">
        <div class="col-md-8">
          <b-nav>
            <b-nav-item :active="isTimelineTracks" :to="{ name: 'user-profile-tracks' }"
            class="border-right pr-3">
              <translate translate-context="Content/UserProfile/Tab/Text">
                Tracks
              </translate>
            </b-nav-item>
            <b-nav-item :active="isTimelineAlbums" :to="{ name: 'user-profile-albums' }"
            class="border-right px-3">
              <translate translate-context="Content/UserProfile/Tab/Text">
                Albums
              </translate>
            </b-nav-item>
            <b-nav-item v-if="isUs" :active="isTimelineDrafts" :to="{ name: 'user-profile-drafts' }"
            class="px-3">
              <translate translate-context="Content/UserProfile/Tab/Text">
                Drafts
              </translate>
            </b-nav-item>
          </b-nav>

          <Timeline v-if="isTimelineTracks"
                    key="{{ userId }}user"
                    timeline-name="user"
                    :user-id="userId"
          />
          <Timeline v-else-if="isTimelineAlbums"
                    key="{{ userId }}albums"
                    timeline-name="albums"
                    :user-id="userId"
          />
          <Timeline v-else-if="isTimelineDrafts"
                    key="{{ userId }}drafts"
                    timeline-name="drafts"
                    :user-id="userId"
          />
        </div>
        <div class="col-md-4">
          <UserCard :user="user" />
          <Footer />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import get from 'lodash/get'
import Timeline from '../timeline/timeline.vue'
import Footer from '../../components/footer/footer.vue'
import UserCard from '../../components/user_card/user_card.vue'

export default {
  components: {
    Timeline,
    UserCard,
    Footer
  },
  data () {
    return {
      error: false,
      userId: null
    }
  },
  computed: {
    user () {
      return this.$store.getters.findUser(this.userId)
    },
    isExternal () {
      return this.$route.name === 'external-user-profile'
    },
    isUs () {
      return this.userId && this.$store.state.users.currentUser.id &&
        this.userId === this.$store.state.users.currentUser.id
    },
    isTimelineTracks () {
      return this.$route.name === 'user-profile-tracks'
    },
    isTimelineAlbums () {
      return this.$route.name === 'user-profile-albums'
    },
    isTimelineDrafts () {
      return this.$route.name === 'user-profile-drafts'
    }
  },
  watch: {
    '$route.params.id': function (newVal) {
      if (newVal) {
        this.cleanUp()
        this.load(newVal)
      }
    },
    '$route.params.name': function (newVal) {
      if (newVal) {
        this.cleanUp()
        this.load(newVal)
      }
    }
  },
  created () {
    const routeParams = this.$route.params
    this.load(routeParams.name || routeParams.id)
  },
  destroyed () {
    this.cleanUp()
  },
  methods: {
    load (userNameOrId) {
      console.debug('loading profile for ' + userNameOrId)
      const user = this.$store.getters.findUser(userNameOrId)
      if (user) {
        this.userId = user.id
        console.warn('we already know the user')
      } else {
        this.$store.dispatch('fetchUser', userNameOrId)
          .then(({ id }) => {
            this.userId = id
            console.warn('fetched by ID: ' + id)
          })
          .catch((reason) => {
            console.warn('cannot fetch user: ' + reason)
            const errorMessage = get(reason, 'error.error')
            if (errorMessage) {
              this.error = errorMessage
            } else {
              let msg = this.$pgettext('Content/UserProfile/Error', 'Error loading user: %{errorMsg}')
              this.error = this.$gettextInterpolate(msg, { errorMsg: errorMessage })
            }
            this.$bvToast.toast(this.$pgettext('Content/UserProfile/Toast/Error/Message', 'Cannot fetch user'), {
              title: this.$pgettext('Content/UserProfile/Toast/Error/Title', 'User Profile'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
          })
      }
    },
    cleanUp () {
      // do nothing for now
    }
  }
}
</script>
