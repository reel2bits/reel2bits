<template>
  <div>
    <div v-if="user">
      Profile of {{ user }}
    </div>
    <div v-if="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import get from 'lodash/get'

export default {
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
        console.warn('load::user::nothing to do')
        // TODO fetch timelines etc.
      } else {
        this.$store.dispatch('fetchUser', userNameOrId)
          .then(({ id }) => {
            this.userId = id
            // TODO same
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
