<template>
  <div class="row justify-content-md-center">
    <div class="col-md-3">
      <b-form class="password-reset-form" @submit.prevent="submit">
        <h1>Reset password</h1>
        <b-form-group
          id="ig-token"
          label="Token:"
          label-for="token"
        >
          <b-form-input
            id="token"
            ref="token"
            v-model="user.token"
            type="text"
            placeholder="Enter token"
            :disabled="isPending"
          />
        </b-form-group>

        <b-form-group
          id="ig-password"
          label="Password:"
          label-for="password"
        >
          <b-form-input
            id="password"
            ref="password"
            v-model="user.password"
            type="password"
            placeholder="Enter password"
            :disabled="isPending"
          />
        </b-form-group>

        <b-form-group
          id="ig-password-confirm"
          label="Confirm password:"
          label-for="password-confirm"
        >
          <b-form-input
            id="password-confirm"
            ref="password-confirm"
            v-model="user.passwordConfirm"
            type="password"
            placeholder="Enter password confirmation"
            :disabled="isPending"
          />
        </b-form-group>

        <b-button type="submit" variant="primary" :disabled="isPending">
          Change
        </b-button>
      </b-form>

      <br>
      <b-alert v-if="error" variant="danger" show
               @dismissed="error = null"
      >
        {{ error }}
      </b-alert>
      <b-alert v-if="success" variant="success" show>
        Password have been changed.
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
    })
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
            this.error = 'Cannot reset password'
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
          this.error = 'Cannot reset password'
        })
    }
  }
}

export default passwordResetToken
</script>
