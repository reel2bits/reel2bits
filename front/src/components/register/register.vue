<template>
  <div>
    <h4>register</h4>
    <form
      class="registration-form"
      @submit.prevent="register(user)"
    >
      <div class="container">
        <div class="text-fields">
          <div
            class="form-group"
            :class="{ 'form-group--error': $v.user.username.$error }"
          >
            <label
              class="form--label"
              for="sign-up-username"
            >username</label>
            <input
              id="sign-up-username"
              v-model.trim="$v.user.username.$model"
              :disabled="isPending"
              class="form-control"
              placeholder="username"
            >
          </div>
          <div
            v-if="$v.user.username.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.user.username.required">
                <span>username required</span>
              </li>
            </ul>
          </div>

          <div
            class="form-group"
            :class="{ 'form-group--error': $v.user.fullname.$error }"
          >
            <label
              class="form--label"
              for="sign-up-fullname"
            >full name</label>
            <input
              id="sign-up-fullname"
              v-model.trim="$v.user.fullname.$model"
              :disabled="isPending"
              class="form-control"
              placeholder="foo bar"
            >
          </div>
          <div
            v-if="$v.user.fullname.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.user.fullname.required">
                <span>full name required</span>
              </li>
            </ul>
          </div>

          <div
            class="form-group"
            :class="{ 'form-group--error': $v.user.email.$error }"
          >
            <label
              class="form--label"
              for="email"
            >email</label>
            <input
              id="email"
              v-model="$v.user.email.$model"
              :disabled="isPending"
              class="form-control"
              type="email"
            >
          </div>
          <div
            v-if="$v.user.email.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.user.email.required">
                <span>email required</span>
              </li>
            </ul>
          </div>

          <div class="form-group">
            <label
              class="form--label"
              for="bio"
            >bio (optional)</label>
            <textarea
              id="bio"
              v-model="user.bio"
              :disabled="isPending"
              class="form-control"
              :placeholder="bioPlaceholder"
            />
          </div>

          <div
            class="form-group"
            :class="{ 'form-group--error': $v.user.password.$error }"
          >
            <label
              class="form--label"
              for="sign-up-password"
            >password</label>
            <input
              id="sign-up-password"
              v-model="user.password"
              :disabled="isPending"
              class="form-control"
              type="password"
            >
          </div>
          <div
            v-if="$v.user.password.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.user.password.required">
                <span>password required</span>
              </li>
            </ul>
          </div>

          <div
            class="form-group"
            :class="{ 'form-group--error': $v.user.confirm.$error }"
          >
            <label
              class="form--label"
              for="sign-up-password-confirmation"
            >confirm password</label>
            <input
              id="sign-up-password-confirmation"
              v-model="user.confirm"
              :disabled="isPending"
              class="form-control"
              type="password"
            >
          </div>
          <div
            v-if="$v.user.confirm.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.user.confirm.required">
                <span>password confirmation required</span>
              </li>
              <li v-if="!$v.user.confirm.sameAsPassword">
                <span>password and confirmation needs to match</span>
              </li>
            </ul>
          </div>
          <div class="form-group">
            <button
              :disabled="isPending"
              type="submit"
              class="btn btn-default"
            >
              submit
            </button>
          </div>
        </div>

        <div
          class="terms-of-service"
          v-html="termsOfService"
        />
      </div>
      <div
        v-if="serverValidationErrors"
        class="form-group"
      >
        <div class="alert error">
          <span
            v-for="error in serverValidationErrors"
            :key="error"
          >{{ error }}</span>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { validationMixin } from 'vuelidate'
import { required, sameAs, maxLength } from 'vuelidate/lib/validators'
import { mapActions, mapState } from 'vuex'

export default {
  mixins: [validationMixin],
  data: () => ({
    user: {
      username: '',
      fullname: '',
      email: '',
      password: '',
      confirm: ''
    }
  }),
  validations: {
    user: {
      email: { required, maxLength: maxLength(250) },
      username: { required, maxLength: maxLength(250) },
      fullname: { required, maxLength: maxLength(250) },
      password: { required, maxLength: maxLength(250) },
      confirm: {
        required,
        maxLength: maxLength(250),
        sameAsPassword: sameAs('password')
      }
    }
  },
  computed: {
    token () { return this.$route.params.token },
    bioPlaceholder () {
      return 'quack quack im a cat'.replace(/\s*\n\s*/g, ' \n')
    },
    ...mapState({
      registrationOpen: (state) => state.instance.registrationOpen,
      signedIn: (state) => !!state.users.currentUser,
      isPending: (state) => state.users.signUpPending,
      serverValidationErrors: (state) => state.users.signUpErrors,
      termsOfService: (state) => state.instance.tos
    })
  },
  created () {
    if ((!this.registrationOpen && !this.token) || this.signedIn) {
      this.$router.push({ name: 'home' })
    }
  },
  methods: {
    ...mapActions(['signUp']),
    async register () {
      this.user.nickname = this.user.username

      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('register:registering')
          await this.signUp(this.user)
          this.$router.push({ name: 'profile' })
        } catch (error) {
          console.warn('Registration failed: ' + error)
        }
      }
    }
  }
}
</script>
