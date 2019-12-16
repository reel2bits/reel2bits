<template>
  <div class="row justify-content-md-center">
    <div class="col-md-4">
      <h4 v-translate translate-context="Content/Register/Headline/Registering">
        Registering
      </h4>

      <b-form class="registration-form" @submit.prevent="register(user)">
        <b-form-group
          id="ig-username"
          :class="{ 'form-group--error': $v.user.username.$error }"
          :label="labels.usernameLabel"
          label-for="username"
        >
          <b-form-input
            id="username"
            v-model.trim="$v.user.username.$model"
            :disabled="isPending"
            :placeholder="labels.usernamePlaceholder"
            :state="$v.user.username.$dirty ? !$v.user.username.$error : null"
            aria-describedby="username-live-feedback"
          />
          <b-form-invalid-feedback id="username-live-feedback">
            <span v-if="!$v.user.username.required" v-translate translate-context="Content/Register/Feedback/Username/Required">Username is required</span>
            <span v-if="!$v.user.username.usernameIsLegal" v-translate translate-context="Content/Register/Feedback/Username/InvalidChars">Username can only contains letters or numbers</span>
            <span v-if="!$v.user.username.usernameNotRestricted" v-translate translate-context="Content/Register/Feedback/Username/RestrictedUsername">This username cannot be used</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-fullname"
          :class="{ 'form-group--error': $v.user.fullname.$error }"
          :label="labels.fullnameLabel"
          label-for="fullname"
        >
          <b-form-input
            id="fullname"
            v-model.trim="$v.user.fullname.$model"
            :disabled="isPending"
            :placeholder="labels.fullnamePlaceholder"
            :state="$v.user.fullname.$dirty ? !$v.user.fullname.$error : null"
            aria-describedby="fullname-live-feedback"
          />
          <b-form-invalid-feedback id="fullname-live-feedback">
            <translate translate-context="Content/Register/Feedback/DisplayName/Required">
              Display name is required
            </translate>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-email"
          :class="{ 'form-group--error': $v.user.email.$error }"
          :label="labels.emailLabel"
          label-for="email"
        >
          <b-form-input
            id="email"
            v-model.trim="$v.user.email.$model"
            :disabled="isPending"
            :placeholder="labels.emailPlaceholder"
            :state="$v.user.email.$dirty ? !$v.user.email.$error : null"
            aria-describedby="email-live-feedback"
          />
          <b-form-invalid-feedback id="email-live-feedback">
            <translate translate-context="Content/Register/Feedback/Email/Required">
              Your email is required
            </translate>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-bio"
          :label="labels.bioLabel"
          label-for="bio"
        >
          <b-form-textarea
            id="bio"
            v-model="user.bio"
            :disabled="isPending"
            :placeholder="labels.bioPlaceholder"
          />
        </b-form-group>

        <b-form-group
          id="ig-password"
          :class="{ 'form-group--error': $v.user.password.$error }"
          :label="labels.passwordLabel"
          label-for="password"
        >
          <b-form-input
            id="password"
            v-model.trim="$v.user.password.$model"
            :disabled="isPending"
            :placeholder="labels.passwordPlaceholder"
            :state="$v.user.password.$dirty ? !$v.user.password.$error : null"
            aria-describedby="password-live-feedback"
            type="password"
          />
          <b-form-invalid-feedback id="password-live-feedback">
            <translate translate-context="Content/Register/Feedback/Password/Required">
              A secure password is required
            </translate>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-password-confirmation"
          :class="{ 'form-group--error': $v.user.confirm.$error }"
          :label="labels.passwordConfirmLabel"
          label-for="password-confirmation"
        >
          <b-form-input
            id="password-confirmation"
            v-model.trim="$v.user.confirm.$model"
            :disabled="isPending"
            :placeholder="labels.passwordConfirmPlaceholder"
            :state="$v.user.confirm.$dirty ? !$v.user.confirm.$error : null"
            aria-describedby="password-confirmation-live-feedback"
            type="password"
          />
          <b-form-invalid-feedback id="password-confirmation-live-feedback">
            <span v-if="!$v.user.confirm.required" v-translate translate-context="Content/Register/Feedback/PasswordConfirm/Required">You need to confirm your password</span>
            <span v-if="!$v.user.confirm.sameAsPassword" v-translate translate-context="Content/Register/Feedback/PasswordConfirm/NotSameAsPassword">Both passwords needs to match</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-button :disabled="isPending" type="submit" variant="primary">
          <translate translate-context="Content/Register/Button/Register">
            Register
          </translate>
        </b-button>
      </b-form>

      <br>
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

const usernameIsLegal = value => {
  return /^[a-zA-Z\d]+$/.test(value)
}

function usernameNotRestricted (value) {
  return !this.$store.state.instance.restrictedNicknames.includes(value)
}

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
      username: { required, maxLength: maxLength(250), usernameIsLegal, usernameNotRestricted },
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
    ...mapState({
      registrationOpen: state => state.instance.registrationOpen,
      signedIn: state => !!state.users.currentUser,
      isPending: state => state.users.signUpPending,
      serverValidationErrors: state => state.users.signUpErrors,
      termsOfService: state => state.instance.tos
    }),
    labels () {
      return {
        usernameLabel: this.$pgettext('Content/Register/Input.Label/Username', 'Username:'),
        usernamePlaceholder: this.$pgettext('Content/Register/Input.Placeholder/Username', 'Enter username'),
        passwordLabel: this.$pgettext('Content/Register/Input.Label/Password', 'Password:'),
        passwordPlaceholder: this.$pgettext('Content/Register/Input.Placeholder/Password', 'Enter password'),
        passwordConfirmLabel: this.$pgettext('Content/Register/Input.Label/PasswordConfirm', 'Confirm password:'),
        passwordConfirmPlaceholder: this.$pgettext('Content/Register/Input.Placeholder/PasswordConfirm', 'Enter password again'),
        fullnameLabel: this.$pgettext('Content/Register/Input.Label/Fullname', 'Display name:'),
        fullnamePlaceholder: this.$pgettext('Content/Register/Input.Placeholder/Fullname', 'your display name'),
        emailLabel: this.$pgettext('Content/Register/Input.Label/Email', 'Email:'),
        emailPlaceholder: this.$pgettext('Content/Register/Input.Placeholder/Email', 'your email'),
        bioLabel: this.$pgettext('Content/Register/Input.Label/Bio', 'Bio (optional):'),
        bioPlaceholder: this.$pgettext('Content/Register/Input.Placeholder/Bio', "quack quack I'm a cat").replace(/\s*\n\s*/g, ' \n')
      }
    }
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
          const autologin = await this.signUp(this.user)
          if (autologin) {
            this.$router.push({ name: 'profile' })
          } else {
            this.$router.push({ name: 'login_form', params: { needsEmailConfirmation: true } })
          }
        } catch (error) {
          console.warn('Registration failed: ' + error)
          this.$bvToast.toast(this.$pgettext('Content/Register/Toast/Error/Message', 'An error occured'), {
            title: this.$pgettext('Content/Register/Toast/Error/Title', 'Registration'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        }
      }
    }
  }
}
</script>
