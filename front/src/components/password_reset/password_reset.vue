<template>
  <div class="row justify-content-md-center">
    <div class="col-md-3">
      <b-form class="password-reset-form" @submit.prevent="submit">
        <h1 v-translate translate-context="Content/PasswordReset/Headline">
          Reset password
        </h1>
        <b-form-group
          id="ig-email"
          :label="labels.emailLabel"
          label-for="email"
        >
          <b-form-input
            id="email"
            ref="email"
            v-model="user.email"
            type="text"
            :placeholder="labels.emailPlaceholder"
            :disabled="isPending"
          />
        </b-form-group>

        <b-button type="submit" variant="primary" :disabled="isPending">
          <translate translate-context="Content/PasswordReset/Button/Send reset email">
            Send reset email
          </translate>
        </b-button>
      </b-form>

      <br>
      <b-alert v-if="error" variant="danger" show
               @dismissed="error = null"
      >
        {{ error }}
      </b-alert>
      <b-alert v-if="success" variant="success" show>
        <translate translate-context="Content/PasswordReset/Alert/Link generated, check emails">
          Link generated with success, check your emails.
        </translate>
      </b-alert>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

const passwordReset = {
  data: () => ({
    user: {
      email: ''
    },
    isPending: false,
    success: false,
    error: null
  }),
  computed: {
    ...mapState({
      signedIn: (state) => !!state.users.currentUser
    }),
    labels () {
      return {
        emailLabel: this.$pgettext('Content/PasswordReset/Input.Label/Email', 'Email:'),
        emailPlaceholder: this.$pgettext('Content/PasswordReset/Input.Placeholder/Email', 'your email')
      }
    }
  },
  created () {
    if (this.signedIn) {
      this.$router.push({ name: 'root' })
    }
  },
  methods: {
    submit () {
      this.isPending = true
      const email = this.user.email
      this.$store.state.api.backendInteractor.resetPassword({ email })
        .then(({ status }) => {
          this.isPending = false
          this.user.email = ''

          if (status === 204) {
            this.success = true
            this.error = null
          } else if (status === 404 || status === 400) {
            this.error = this.$pgettext('Content/PasswordReset/Error', 'Cannot generate reset link')
            this.$bvToast.toast(this.$pgettext('Content/PasswordReset/Toast/Error/Message', 'Cannot generate reset link'), {
              title: this.$pgettext('Content/PasswordReset/Toast/Error/Title', 'Password Reset'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
            this.$nextTick(() => {
              this.$refs.email.focus()
            })
          }
        })
        .catch(() => {
          this.isPending = false
          this.user.email = ''
          this.error = this.$pgettext('Content/PasswordReset/Error', 'Cannot generate reset link')
          this.$bvToast.toast(this.$pgettext('Content/PasswordReset/Toast/Error/Message', 'Cannot generate reset link'), {
            title: this.$pgettext('Content/PasswordReset/Toast/Error/Title', 'Password Reset'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'danger'
          })
        })
    }
  }
}

export default passwordReset
</script>
