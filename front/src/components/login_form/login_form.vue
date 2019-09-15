<template>
  <div class="row justify-content-md-center">
    <div class="col-md-3">
      <b-form class="login" @submit.prevent="submitPassword">
        <h1 v-translate>
          Sign in
        </h1>
        <b-form-group
          id="ig-username"
          :label="labels.usernameLabel"
          label-for="username"
        >
          <b-form-input
            id="username"
            v-model="user.username"
            type="text"
            :placeholder="labels.usernamePlaceholder"
            :state="$v.user.username.$dirty ? !$v.user.username.$error : null"
            aria-describedby="login-live-feedback"
          />
          <b-form-invalid-feedback id="login-live-feedback">
            <translate translate-context="Content/Login/Feedback/Username/Required">
              Please enter your login
            </translate>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-password"
          :label="labels.passwordLabel"
          label-for="password"
        >
          <b-form-input
            id="password"
            v-model="user.password"
            type="password"
            :placeholder="labels.passwordPlaceholder"
            :state="$v.user.password.$dirty ? !$v.user.password.$error : null"
            aria-describedby="password-live-feedback"
          />
          <b-form-invalid-feedback id="password-live-feedback">
            <translate translate-context="Content/Login/Feedback/Password/Required">
              Please enter your password
            </translate>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-button type="submit" variant="primary">
          <translate translate-context="Content/Login/Button/Login">
            Login
          </translate>
        </b-button>
        <router-link :to="{name: 'password-reset'}">
          <translate translate-context="Content/Login/Link/Reset password">
            Reset password
          </translate>
        </router-link>
      </b-form>

      <br>
      <b-alert v-if="error" variant="danger" show>
        {{ error }}
      </b-alert>
    </div>
  </div>
</template>

<script>
import { validationMixin } from 'vuelidate'
import { required, maxLength } from 'vuelidate/lib/validators'
import { mapState, mapActions } from 'vuex'
import oauthApi from '../../backend/oauth/oauth.js'

export default {
  mixins: [validationMixin],
  data: () => ({
    user: {},
    error: false
  }),
  validations: {
    user: {
      username: { required, maxLength: maxLength(250) },
      password: { required, maxLength: maxLength(250) }
    }
  },
  computed: {
    ...mapState({
      registrationOpen: state => state.instance.registrationOpen,
      instance: state => state.instance,
      loggingIn: state => state.users.loggingIn,
      oauth: state => state.oauth
    }),
    labels () {
      return {
        usernameLabel: this.$pgettext('Content/Login/Input.Label/Username', 'Username:'),
        usernamePlaceholder: this.$pgettext('Content/Login/Input.Placeholder/Username', 'Enter username'),
        passwordLabel: this.$pgettext('Content/Login/Input.Label/Password', 'Password:'),
        passwordPlaceholder: this.$pgettext('Content/Login/Input.Placeholder/Password', 'Enter password')
      }
    }
  },
  methods: {
    ...mapActions({ login: 'authFlow/login' }),
    submitPassword: function () {
      this.$v.$touch()

      if (this.$v.$invalid) {
        return
      }

      const { clientId } = this.oauth
      const data = {
        clientId,
        oauth: this.oauth,
        commit: this.$store.commit
      }
      this.error = false

      // Get or create App
      // Then authorize to get code
      // And finally get the bearer from token

      oauthApi.getOrCreateApp(data).then(app => {
        oauthApi
          .getTokenWithCredentials({
            ...app,
            instance: data.instance,
            username: this.user.username,
            password: this.user.password
          })
          .then(result => {
            if (result.error) {
              this.error = result.error
              this.focusOnPasswordInput()
              return
            }
            this.login(result).then(() => {
              this.$router.push({ name: 'friends' })
            })
          })
          .catch(error => {
            console.error('Unhandled error: ' + error)
            this.error = this.$pgettext('Content/Login/Error/Occured', 'An error occured, please try again later')
            this.$bvToast.toast(this.$pgettext('Content/TrackAlbum/Toast/Error/Message', 'An error occured, please try again later'), {
              title: this.$pgettext('Content/TrackAlbum/Toast/Error/Title', 'Login'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
          })
      })
    },
    clearError () {
      this.error = false
    },
    focusOnPasswordInput () {
      let passwordInput = this.$refs.passwordInput
      passwordInput.focus()
      passwordInput.setSelectionRange(0, passwordInput.value.length)
    }
  }
}
</script>
