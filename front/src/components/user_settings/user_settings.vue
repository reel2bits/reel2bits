<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-tabs content="mt-3">
        <!-- settings -->
        <b-tab :title="labels.userSettingsTab">
          <b-alert v-if="saveError" variant="danger" show>
            <span v-translate translate-context="Content/UserSettings/Alert/Error saving">Error saving settings.</span>
          </b-alert>

          <b-alert v-if="saveOk" variant="success" :show="5"
                   dismissible fade
                   @dismissed="saveOk=false"
          >
            <span v-translate translate-context="Content/UserSettings/Alert/Success saving">Settings saved.</span>
          </b-alert>

          <b-form class="edit-track-form" @submit.prevent="save(user)">
            <b-form-group
              id="ig-fullname"
              :class="{ 'form-group--error': $v.user.fullname.$error }"
              :label="labels.fullnameLabel"
              label-for="fullname"
            >
              <b-form-input
                id="fullname"
                v-model.trim="$v.user.fullname.$model"
                :placeholder="labels.fullnamePlaceholder"
                :state="$v.user.fullname.$dirty ? !$v.user.fullname.$error : null"
                aria-describedby="fullname-live-feedback"
              />
              <b-form-invalid-feedback id="fullname-live-feedback">
                <translate translate-context="Content/UserSettings/Feedback/DisplayName/Required">
                  Display name is required
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
                :placeholder="labels.bioPlaceholder"
              />
            </b-form-group>

            <b-form-group
              id="ig-lang"
              :label="labels.langLabel"
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
              <translate translate-context="Content/UserSettings/Button/Save">
                Save
              </translate>
            </b-button>

            <hr>

            <div class="row">
              <div class="col-sm-6">
                <p v-translate translate-context="Content/UserSettings/Text/Avatar picker" class="visibility-notice">
                  The recommended minimum size for avatar pictures is 112x112 pixels. JPEG, PNG or GIF only.
                </p>
                <p v-translate translate-context="Content/UserSettings/Title/Avatar picker">
                  Current avatar
                </p>
                <img
                  :src="currentAvatar"
                  class="current-avatar"
                  width="112"
                  height="112"
                >
              </div>
              <div class="col-sm-6">
                <p v-translate translate-context="Content/UserSettings/Title/Avatar picker">
                  Set new avatar
                </p>
                <b-button
                  v-show="pickAvatarBtnVisible"
                  id="pick-avatar"
                >
                  <translate translate-context="Content/UserSettings/Button/Avatar picker">
                    Upload an image
                  </translate>
                </b-button>

                <image-cropper
                  trigger="#pick-avatar"
                  :submit-handler="submitAvatar"
                  @open="pickAvatarBtnVisible=false"
                  @close="pickAvatarBtnVisible=true"
                />
              </div>
            </div>
          </b-form>
        </b-tab>

        <!-- security -->
        <b-tab :title="labels.securityTab">
          <b-form-group
            id="ig-password0"
            :label="labels.passwordLabel"
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
            :label="labels.passwordNewLabel"
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
            :label="labels.passwordNewConfirmLabel"
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
            <translate translate-context="Content/UserSettings/Button/Change password">
              Change password
            </translate>
          </b-button>

          <p v-if="changedPassword">
            <translate translate-context="Content/UserSettings/Alert/Password changed">
              Password changed
            </translate>
          </p>
          <p v-else-if="changePasswordError !== false">
            <translate translate-context="Content/UserSettings/Alert/Password change error">
              Error changing password
            </translate>
          </p>
          <p v-if="changePasswordError">
            {{ changePasswordError }}
          </p>
        </b-tab>

        <!-- account -->
        <b-tab :title="labels.accountTab">
          <b-button v-b-modal.modal-delete
                    variant="danger"
          >
            <i class="fa fa-times" aria-hidden="true" /> <translate translate-context="Content/UserSettings/Button">
              Delete my account
            </translate>
          </b-button>
          <b-modal id="modal-delete" :title="labels.deleteAccountModalTitle" @ok="deleteAccount">
            <p v-translate class="my-4" translate-context="Content/UserSettings/Modal/Delete/Content">
              Are you sure you want to delete your account ?
              <br>
              All associated datas will be permanently deleted.
            </p>
          </b-modal>
        </b-tab>
      </b-tabs>
    </div>
  </div>
</template>

<style lang="scss">
ul.nav-tabs {
  margin-bottom: .5em;
}
</style>

<script>
import { validationMixin } from 'vuelidate'
import { required, maxLength } from 'vuelidate/lib/validators'
import locales from '../../locales.js'
import ImageCropper from '../../components/image_cropper/image_cropper.vue'

export default {
  components: {
    ImageCropper
  },
  mixins: [validationMixin],
  data: () => ({
    user: {
      lang: '',
      fullname: '',
      bio: ''
    },
    saveError: false,
    saveOk: false,
    changePasswordInputs: ['', '', ''],
    changedPassword: false,
    changePasswordError: false,
    pickAvatarBtnVisible: true
  }),
  validations: {
    user: {
      fullname: { required, maxLength: maxLength(250) }
    }
  },
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    availableLangs () {
      return locales.locales.map(e => { return { value: e.code, text: e.label } })
    },
    labels () {
      return {
        langLabel: this.$pgettext('Content/UserSettings/Input.Label/Lang', 'Language:'),
        passwordLabel: this.$pgettext('Content/UserSettings/Input.Label/Password', 'Current password:'),
        passwordNewLabel: this.$pgettext('Content/UserSettings/Input.Label/PasswordNew', 'New password:'),
        passwordNewConfirmLabel: this.$pgettext('Content/UserSettings/Input.Label/PasswordNewConfirm', 'Confirm new password:'),
        fullnameLabel: this.$pgettext('Content/UserSettings/Input.Label/Fullname', 'Display name:'),
        fullnamePlaceholder: this.$pgettext('Content/UserSettings/Input.Placeholder/Fullname', 'your display name'),
        bioLabel: this.$pgettext('Content/UserSettings/Input.Label/Bio', 'Bio (optional):'),
        bioPlaceholder: this.$pgettext('Content/UserSettings/Input.Placeholder/Bio', "quack quack I'm a cat").replace(/\s*\n\s*/g, ' \n'),
        userSettingsTab: this.$pgettext('Content/UserSettings/Tabs/Label', 'User settings'),
        securityTab: this.$pgettext('Content/UserSettings/Tabs/Label', 'Security'),
        accountTab: this.$pgettext('Content/UserSettings/Tabs/Label', 'Account'),
        deleteAccountModalTitle: this.$pgettext('Content/UserSettings/Modal/Title', 'Account deletion')
      }
    },
    currentAvatar () {
      if (this.currentUser && this.currentUser.profile_image_url) {
        return this.currentUser.profile_image_url
      } else {
        return '/static/userpic_placeholder.svg'
      }
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
            this.$store.dispatch('setOption', { name: 'interfaceLanguage', value: this.user.lang })
            this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'Saved !'), {
              title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Settings'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'success'
            })
          })
          .catch((e) => {
            console.log('Cannot save settings: ' + e)
            this.saveError = true
            this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'Error saving settings'), {
              title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Settings'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
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
            this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'Password changed !'), {
              title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Password'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'success'
            })
            this.changedPassword = true
            this.changePasswordError = false
            this.logout()
          } else {
            this.changedPassword = false
            this.changePasswordError = res.error
            this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'Error changing password'), {
              title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Password'),
              autoHideDelay: 5000,
              appendToast: false,
              variant: 'danger'
            })
          }
        })
    },
    logout () {
      this.$store.dispatch('logout')
      this.$router.replace('/')
    },
    async deleteAccount () {
      console.log('deleting account')
      await this.$store.state.api.backendInteractor.deleteUser({ userId: this.currentUser.id })
        .then(() => {
          console.log('account deletion queued')
          this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'Action in progress'), {
            title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Account deletion'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'success'
          })
          this.logout()
        })
        .catch((e) => {
          console.log('an error occured', e)
          this.$bvToast.toast(this.$pgettext('Content/UserSettings/Toast/Error/Message', 'An error occured while deleting the account'), {
            title: this.$pgettext('Content/UserSettings/Toast/Error/Title', 'Account deletion'),
            autoHideDelay: 20000,
            appendToast: false,
            variant: 'danger'
          })
        })
    },
    submitAvatar (cropper, file) {
      const that = this
      return new Promise((resolve, reject) => {
        function updateAvatar (avatar) {
          that.$store.state.api.backendInteractor.updateAvatar({ avatar })
            .then((user) => {
              that.$store.commit('addNewUsers', [user])
              that.$store.commit('setCurrentUser', user)
              resolve()
            })
            .catch((err) => {
              reject(new Error(that.$t('upload.error.base') + ' ' + err.message))
            })
        }

        if (cropper) {
          cropper.getCroppedCanvas().toBlob(updateAvatar, file.type)
        } else {
          updateAvatar(file)
        }
      })
    }
  }
}
</script>
