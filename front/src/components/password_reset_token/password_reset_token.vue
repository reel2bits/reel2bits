<template>
  <div class="row justify-content-md-center">
    <div class="col-md-3">
      <b-form class="password-reset-form" @submit.prevent="submit">
        <h1 v-translate translate-context="Content/PasswordResetToken/Headline/Reset password">
          Reset password
        </h1>

        <b-form-group
          id="ig-password"
          :label="labels.passwordLabel"
          label-for="password"
        >
          <b-form-input
            id="password"
            ref="password"
            v-model="user.password"
            type="password"
            :placeholder="labels.passwordPlaceholder"
            :disabled="isPending"
          />
        </b-form-group>

        <b-form-group
          id="ig-password-confirm"
          :label="labels.passwordConfirmLabel"
          label-for="password-confirm"
        >
          <b-form-input
            id="password-confirm"
            ref="password-confirm"
            v-model="user.passwordConfirm"
            type="password"
            :placeholder="labels.passwordConfirmPlaceholder"
            :disabled="isPending"
          />
        </b-form-group>

        <b-button type="submit" variant="primary" :disabled="isPending">
          <translate translate-context="Content/PasswordResetToken/Button/Change password">
            Change password
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
        <translate translate-context="Content/PasswordResetToken/Alert/Password changed">
          Password have been changed.
        </translate>
      </b-alert>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

const passwordResetToken = {
  data: () => ({
    user: {
      token: '',
      password: '',
      passwordConfirm: ''
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
        passwordLabel: this.$pgettext('Content/PasswordResetToken/Input.Label/Password', 'Password:'),
        passwordPlaceholder: this.$pgettext('Content/PasswordResetToken/Input.Placeholder/Password', 'Enter password'),
        passwordConfirmLabel: this.$pgettext('Content/PasswordResetToken/Input.Label/PasswordConfirm', 'Confirm password:'),
        passwordConfirmPlaceholder: this.$pgettext('Content/PasswordResetToken/Input.Placeholder/PasswordConfirm', 'Enter password again')
      }
    }
  },
  created () {
    if (this.signedIn) {
      this.$router.push({ name: 'root' })
    }
    this.user.token = (this.$route.params.token || '')
    this.$nextTick(() => {
      this.$refs.password.focus()
    })
  },
  methods: {
    submit () {
      this.isPending = true
      const token = this.user.token
      const password = this.user.password
      const passwordConfirm = this.user.passwordConfirm
      this.$store.state.api.backendInteractor.resetPasswordToken({ token, password, passwordConfirm })
        .then(({ status }) => {
          this.isPending = false
          this.user.token = ''
          this.user.password = ''
          this.user.passwordConfirm = ''

          if (status === 204) {
            this.success = true
            this.error = null
          } else if (status === 404 || status === 400 || status === 500) {
            this.error = this.$pgettext('Content/PasswordResetToken/Errors/Cannot reset', 'Cannot reset password')
            this.$bvToast.toast(this.$pgettext('Content/PasswordResetToken/Toast/Error/Message', 'Cannot reset password'), {
              title: this.$pgettext('Content/PasswordResetToken/Toast/Error/Title', 'Password Reset'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
            this.$nextTick(() => {
              this.$refs.token.focus()
            })
          }
        })
        .catch(() => {
          this.isPending = false
          this.user.email = ''
          this.user.password = ''
          this.user.passwordConfirm = ''
          this.error = this.$pgettext('Content/PasswordResetToken/Errors/Cannot reset', 'Cannot reset password')
          this.$bvToast.toast(this.$pgettext('Content/PasswordResetToken/Toast/Error/Message', 'Cannot reset password'), {
            title: this.$pgettext('Content/PasswordResetToken/Toast/Error/Title', 'Password Reset'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'danger'
          })
        })
    }
  }
}

export default passwordResetToken
</script>
