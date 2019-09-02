<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-tabs content="mt-3">
        <b-tab title="User settings">
          <b-alert v-if="saveError" variant="danger" show>
            <span>Error saving settings.</span>
          </b-alert>

          <b-alert v-if="saveOk" variant="success" :show="5"
                   dismissible fade
                   @dismissed="saveOk=false"
          >
            <span>Settings saved.</span>
          </b-alert>

          <b-form class="edit-track-form" @submit.prevent="save(user)">
            <b-form-group
              id="ig-fullname"
              :class="{ 'form-group--error': $v.user.fullname.$error }"
              label="Display name:"
              label-for="fullname"
            >
              <b-form-input
                id="fullname"
                v-model.trim="$v.user.fullname.$model"
                placeholder="display name"
                :state="$v.user.fullname.$dirty ? !$v.user.fullname.$error : null"
                aria-describedby="fullname-live-feedback"
              />
              <b-form-invalid-feedback id="fullname-live-feedback">
                Display name is required
              </b-form-invalid-feedback>
            </b-form-group>
            ba
            <b-form-group
              id="ig-bio"
              label="Bio (optional):"
              label-for="bio"
            >
              <b-form-textarea
                id="bio"
                v-model="user.bio"
                :placeholder="bioPlaceholder"
              />
            </b-form-group>

            <b-form-group
              id="ig-lang"
              label="Lang:"
              label-for="lang"
            >
              <b-form-select
                id="lang"
                v-model="user.lang"
                :options="availableLangs"
              />
            </b-form-group>

            <br>

            <b-button type="submit" variant="primary">
              Save
            </b-button>
          </b-form>
        </b-tab>
        <b-tab title="Security">
          <b-form-group
            id="ig-password0"
            label="Current password:"
            label-for="password0"
          >
            <b-form-input
              id="password0"
              v-model="changePasswordInputs[0]"
              type="password"
            />
          </b-form-group>

          <b-form-group
            id="ig-password1"
            label="New password:"
            label-for="password1"
          >
            <b-form-input
              id="password1"
              v-model="changePasswordInputs[1]"
              type="password"
            />
          </b-form-group>

          <b-form-group
            id="ig-password2"
            label="Confirm new password:"
            label-for="password2"
          >
            <b-form-input
              id="password2"
              v-model="changePasswordInputs[2]"
              type="password"
            />
          </b-form-group>

          <b-button
            variant="primary"
            @click="changePassword"
          >
            Change password
          </b-button>

          <p v-if="changedPassword">
            Password changed
          </p>
          <p v-else-if="changePasswordError !== false">
            Error changing password
          </p>
          <p v-if="changePasswordError">
            {{ changePasswordError }}
          </p>
        </b-tab>
      </b-tabs>
    </div>
  </div>
</template>

<script>
import { validationMixin } from 'vuelidate'
import { required, maxLength } from 'vuelidate/lib/validators'

export default {
  mixins: [validationMixin],
  data: () => ({
    user: {
      lang: '',
      fullname: '',
      bio: ''
    },
    saveError: false,
    saveOk: false,
    changePasswordInputs: [ '', '', '' ],
    changedPassword: false,
    changePasswordError: false
  }),
  validations: {
    user: {
      fullname: { required, maxLength: maxLength(250) }
    }
  },
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    availableLangs () {
      return [
        { value: 'en', text: 'English' },
        { value: 'fr', text: 'French' }
      ]
    },
    bioPlaceholder () {
      return 'quack quack i\'m a cat'.replace(/\s*\n\s*/g, ' \n')
    }
  },
  created () {
    this.user.fullname = this.currentUser.name
    this.user.bio = this.currentUser.description
    this.user.lang = this.currentUser.reel2bits.lang
  },
  methods: {
    async save () {
      console.log('saving settings')
      this.$v.$touch()
      if (!this.$v.$invalid) {
        await this.$store.state.api.backendInteractor.updateUserSettings({ settings: this.user })
          .then((user) => {
            this.$store.commit('addNewUsers', [user])
            this.$store.commit('setCurrentUser', user)
            this.saveOk = true
          })
          .catch((e) => {
            console.log('Cannot save settings: ' + e)
            this.saveError = true
          })
      }
    },
    changePassword () {
      const params = {
        password: this.changePasswordInputs[0],
        newPassword: this.changePasswordInputs[1],
        newPasswordConfirmation: this.changePasswordInputs[2]
      }
      this.$store.state.api.backendInteractor.changePassword(params)
        .then((res) => {
          if (res.status === 'success') {
            this.changedPassword = true
            this.changePasswordError = false
            this.logout()
          } else {
            this.changedPassword = false
            this.changePasswordError = res.error
          }
        })
    },
    logout () {
      this.$store.dispatch('logout')
      this.$router.replace('/')
    }
  }
}
</script>
