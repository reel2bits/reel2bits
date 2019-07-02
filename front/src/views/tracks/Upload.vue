<template>
    <div>
      <h4>Upload a new track</h4>
      <form v-on:submit.prevent='upload(track)' class='upload-track-form'>
        <div class='container'>
          <div class='text-fields'>
            <div class='form-group' :class="{ 'form-group--error': $v.track.title.$error }">
              <label class='form--label' for='track-upload-title'>title</label>
              <input :disabled="isPending" v-model.trim='$v.track.title.$model' class='form-control' id='track-upload-title' placeholder="title">
            </div>
            <div class="form-error" v-if="$v.track.title.$dirty">
              <ul>
                <li v-if="!$v.track.title.required">
                  <span>title required</span>
                </li>
              </ul>
            </div>

            <div class='form-group'>
              <label class='form--label' for='description'>description</label>
              <textarea :disabled="isPending" v-model='track.description' class='form-control' id='description' :placeholder="descriptionPlaceholder"></textarea>
            </div>

            <div class='form-group'>
              <label class='form--label' for='file'>file</label>
              <input type='file' name='file' required="" :disabled="isPending" @change='processFile($event)' class='form-control-file' id='file'>
            </div>
            <div class="form-error" v-if="$v.track.file.$dirty">
              <ul>
                <li v-if="!$v.track.file.required">
                  <span>file required</span>
                </li>
              </ul>
            </div>

            <div class='form-group'>
              <label class='form--label' for='licence'>licence</label>
              <select class="form-control" id="licence" name="licence">
                <option value="0">Not Specified</option>
                <option value="1">CC Attribution</option>
                <option value="2">CC Attribution Share Alike</option>
                <option value="3">CC Attribution No Derivatives</option>
                <option value="4">CC Attribution Non Commercial</option>
                <option value="5">CC Attribution Non Commercial - Share Alike</option>
                <option value="6">CC Attribution Non Commercial - No Derivatives</option>
                <option value="7">Public Domain Dedication</option>
              </select>
            </div>

            <div class='form-group'>
              <label class='form--label' for='private'>private</label>
              <input type='checkbox' name='private' value='y' :disabled="isPending" v-model='track.private' class='form-control' id='private'>
            </div>

            <div class='form-group'>
              <button :disabled="isPending" type='submit' class='btn btn-default'>upload</button>
            </div>
          </div>

        </div>
        <div v-if="serverValidationErrors" class='form-group'>
          <div class='alert error'>
            <span v-for="error in serverValidationErrors" :key="error">{{error}}</span>
          </div>
        </div>
      </form>
    </div>
</template>

<script>
import { validationMixin } from 'vuelidate'
import { required } from 'vuelidate/lib/validators'
import { mapState } from 'vuex'

export default {
  state: {
    uploadPending: false,
    uploadErrors: []
  },
  mixins: [validationMixin],
  data: () => ({
    track: {
      title: '',
      description: '',
      file: '',
      album: '',
      licence: '',
      private: '',
      confirm: ''
    }
  }),
  validations: {
    track: {
      title: { },
      description: { },
      file: { required },
      album: { required },
      licence: { required },
      private: { },
      confirm: {
        required
      }
    }
  },
  created () {
    console.log('upload view created() called')
    if (!this.signedIn) {
      console.debug('not logged in, redirecting')
      this.$router.push({ name: 'home' })
    }
  },
  computed: {
    token () { return this.$route.params.token },
    descriptionPlaceholder () {
      return 'Optional, what is this track about ?'
    },
    ...mapState({
      signedIn: (state) => !!state.users.currentUser,
      isPending: (state) => state.uploadPending,
      serverValidationErrors: (state) => state.uploadErrors
    })
  },
  methods: {
    async upload () {
      console.warn('IMPLEMENT ME')
    }
  }
}
</script>
