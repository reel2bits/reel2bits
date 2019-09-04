<template>
  <div class="row justify-content-md-center">
    <div class="col-md-3">
      <b-form class="password-reset-form" @submit.prevent="submit">
        <h1>Reset password</h1>
        <b-form-group
          id="ig-email"
          label="Email:"
          label-for="email"
        >
          <b-form-input
            id="email"
            ref="email"
            v-model="user.email"
            type="text"
            placeholder="Enter email"
            :disabled="isPending"
          />
        </b-form-group>

        <b-button type="submit" variant="primary" :disabled="isPending">
          Send reset email
        </b-button>
      </b-form>

      <br>
      <b-alert v-if="error" variant="danger" show
               @dismissed="error = null"
      >
        {{ error }}
      </b-alert>
      <b-alert v-if="success" variant="success" show>
        Link generated with success, check your emails.
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
    })
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
            this.error = 'Cannot generate reset link'
            this.$nextTick(() => {
              this.$refs.email.focus()
            })
          }
        })
        .catch(() => {
          this.isPending = false
          this.user.email = ''
          this.error = 'Cannot generate reset link'
        })
    }
  }
}

export default passwordReset
</script>
