<template>
  <div>
    <form class="login" @submit.prevent="submitPassword">
      <h1>Sign in</h1>
      <label>username</label>
      <input required v-model="user.username" type="text" placeholder="Username">
      <label>password</label>
      <input required v-model="user.password" type="password" placeholder="Password" ref='passwordInput'>
      <hr>
      <button type="submit">login</button>
    </form>

    <div v-if="error" class='form-group'>
      <div class='alert error'>
        {{error}}
        <i class="button-icon icon-cancel" @click="clearError"></i>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import oauthApi from '../../backend/oauth/oauth.js'

export default {
  data: () => ({
    user: {},
    error: false
  }),
  computed: {
    ...mapState({
      registrationOpen: state => state.instance.registrationOpen,
      instance: state => state.instance,
      loggingIn: state => state.users.loggingIn,
      oauth: state => state.oauth
    })
  },
  methods: {
    submitPassword: function () {
      const { clientId } = this.oauth
      const data = {
        clientId,
        oauth: this.oauth,
        instance: this.instance.instanceUrl,
        commit: this.$store.commit
      }

      // Get or create App
      // Then authorize to get code
      // And finally get the bearer from token

      oauthApi.getOrCreateApp(data).then((app) => {
        oauthApi.getTokenWithCredentials(
          {
            ...app,
            instance: data.instance,
            username: this.user.username,
            password: this.user.password
          }
        ).then((result) => {
          if (result.error) {
            this.error = result.error
            this.focusOnPasswordInput()
            return
          }
          this.login(result).then(() => {
            this.$router.push({ name: 'profil' })
          })
        })
      })
    },
    clearError () { this.error = false },
    focusOnPasswordInput () {
      let passwordInput = this.$refs.passwordInput
      passwordInput.focus()
      passwordInput.setSelectionRange(0, passwordInput.value.length)
    }
  }
}
</script>
