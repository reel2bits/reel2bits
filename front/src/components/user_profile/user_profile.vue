<template>
  <div>
    <div v-if="error">
      {{ error }}
    </div>
    <div v-if="user">
      <div class="row">
        <div class="col-md-8">
          <b-tabs v-model="tabIndex" content="mt-3">
            <b-tab title="Tracks">
              <Timeline
                key="{{ userId }}user"
                timeline-name="user"
                :user-id="userId"
              />
            </b-tab>
            <b-tab title="Albums">
              <Timeline
                key="{{ userId }}albums"
                timeline-name="albums"
                :user-id="userId"
              />
            </b-tab>
            <b-tab v-if="isUs" title="Drafts">
              <Timeline
                key="{{ userId }}drafts"
                timeline-name="drafts"
                :user-id="userId"
              />
            </b-tab>
          </b-tabs>
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
      userId: null,
      tabIndex: 0,
      tabs: ['user-profile-tracks', 'user-profile-albums']
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
  mounted () {
    console.log(this.$route.name)
    this.tabIndex = this.tabs.findIndex(tab => tab === this.$route.name)
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
        console.warn('load::user::nothing to do')
      } else {
        this.$store.dispatch('fetchUser', userNameOrId)
          .then(({ id }) => {
            this.userId = id
            console.warn('load::!user::fetchUser::id::nothing to do')
          })
          .catch((reason) => {
            console.warn('load::!user::fetchUser::!id')
            const errorMessage = get(reason, 'error.error')
            if (errorMessage) {
              this.error = errorMessage
            } else {
              this.error = 'Error loading user: ' + errorMessage
            }
          })
      }
    },
    cleanUp () {
      // do nothing for now
    }
  }
}
</script>
