<template>
  <div class="row justify-content-md-center">
    <div class="col-md-4">
      <h4>Registering</h4>

      <b-form class="registration-form" @submit.prevent="register(user)">
        <b-form-group
          id="ig-username"
          :class="{ 'form-group--error': $v.user.username.$error }"
          label="Username:"
          label-for="username"
        >
          <b-form-input
            id="username"
            v-model.trim="$v.user.username.$model"
            :disabled="isPending"
            placeholder="username"
            :state="$v.user.username.$dirty ? !$v.user.username.$error : null"
            aria-describedby="username-live-feedback"
          />
          <b-form-invalid-feedback id="username-live-feedback">
            Username is required
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-fullname"
          :class="{ 'form-group--error': $v.user.fullname.$error }"
          label="Display name:"
          label-for="fullname"
        >
          <b-form-input
            id="fullname"
            v-model.trim="$v.user.fullname.$model"
            :disabled="isPending"
            placeholder="display name"
            :state="$v.user.fullname.$dirty ? !$v.user.fullname.$error : null"
            aria-describedby="fullname-live-feedback"
          />
          <b-form-invalid-feedback id="fullname-live-feedback">
            Display name is required
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-email"
          :class="{ 'form-group--error': $v.user.email.$error }"
          label="Email:"
          label-for="email"
        >
          <b-form-input
            id="email"
            v-model.trim="$v.user.email.$model"
            :disabled="isPending"
            placeholder="email"
            :state="$v.user.email.$dirty ? !$v.user.email.$error : null"
            aria-describedby="email-live-feedback"
          />
          <b-form-invalid-feedback id="email-live-feedback">
            Your email is required
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-bio"
          label="Bio (optional):"
          label-for="bio"
        >
          <b-form-textarea
            id="bio"
            v-model="user.bio"
            :disabled="isPending"
            :placeholder="bioPlaceholder"
          />
        </b-form-group>

        <div class="form-group" :class="{ 'form-group--error': $v.user.password.$error }">
          <label class="form--label" for="sign-up-password">Password:</label>
          <input id="sign-up-password" v-model="user.password" :disabled="isPending"
                 class="form-control" type="password"
          >
        </div>
        <div v-if="$v.user.password.$dirty" class="form-error">
          <ul>
            <li v-if="!$v.user.password.required">
              <span>password required</span>
            </li>
          </ul>
        </div>

        <div class="form-group" :class="{ 'form-group--error': $v.user.confirm.$error }">
          <label class="form--label" for="sign-up-password-confirmation">Confirm password:</label>
          <input id="sign-up-password-confirmation" v-model="user.confirm" :disabled="isPending"
                 class="form-control" type="password"
          >
        </div>
        <div v-if="$v.user.confirm.$dirty" class="form-error">
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
          <b-button :disabled="isPending" type="submit" variant="primary">
            Register
          </b-button>
        </div>
      </b-form>

      <b-alert v-if="serverValidationErrors.length > 0" variant="danger" show>
        <span v-for="error in serverValidationErrors" :key="error">{{ error }}</span>
      </b-alert>
    </div>

    <div class="col-md-4">
      <div class="terms-of-service" v-html="termsOfService" />
    </div>
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
    token () {
      return this.$route.params.token
    },
    bioPlaceholder () {
      return 'quack quack i\'m a cat'.replace(/\s*\n\s*/g, ' \n')
    },
    ...mapState({
      registrationOpen: state => state.instance.registrationOpen,
      signedIn: state => !!state.users.currentUser,
      isPending: state => state.users.signUpPending,
      serverValidationErrors: state => state.users.signUpErrors,
      termsOfService: state => state.instance.tos
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
