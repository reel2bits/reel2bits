<template>
    <div>
      <h4>Upload a new track</h4>
      <form v-on:submit.prevent='upload(track)' class='upload-track-form' enctype='multipart/form-data'>
        <div class='container'>
          <div class='text-fields'>
            <div class='form-group' :class="{ 'form-group--error': $v.track.title.$error }">
              <label class='form--label' for='track-upload-title'>title</label>
              <input :disabled="isPending" v-model.trim='$v.track.title.$model' class='form-control' id='track-upload-title' placeholder="title">
            </div>

            <div class='form-group'>
              <label class='form--label' for='description'>description</label>
              <textarea :disabled="isPending" v-model='track.description' class='form-control' id='description' :placeholder="descriptionPlaceholder"></textarea>
            </div>

            <div class='form-group'>
              <label class='form--label' for='file'>file</label>
              <input :accept='acceptedMimeTypes' type='file' name='file' required="" :disabled="isPending" @change='uploadFile($event)' class='form-control-file' id='file'>
            </div>
            <div class="form-error" v-if="$v.track.file.$dirty">
              <ul>
                <li v-if="!$v.track.file.required">
                  <span>file required</span>
                </li>
              </ul>
            </div>
            <div class="form-error" v-if="trackUploadError">
              Error: {{ trackUploadError }}
            </div>

            <!-- TODO: album -->

            <div class='form-group'>
              <label class='form--label' for='licence'>licence</label>
              <select v-model='track.licence' class="form-control" id="licence" name="licence">
                <option v-for='lic in licenceChoices' v-bind:value='lic.value' v-bind:key='lic.value'>{{ lic.text }}</option>
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
import { required, maxLength } from 'vuelidate/lib/validators'
import { mapState, mapActions } from 'vuex'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'

export default {
  ...mapActions(['trackUpload']),
  mixins: [validationMixin],
  data: () => ({
    trackUploadError: '',
    track: {
      title: '',
      description: '',
      file: '',
      // album: '',
      licence: 0,
      private: ''
    }
  }),
  validations: {
    track: {
      title: { maxLength: maxLength(250) },
      description: { },
      file: { required },
      // album: { required },
      licence: { required },
      private: { }
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
    descriptionPlaceholder () {
      return 'Optional, what is this track about ?'
    },
    acceptedMimeTypes () {
      const mp3 = ['audio/mpeg3', 'audio/x-mpeg-3']
      const ogg = ['audio/ogg', 'audio/x-ogg']
      const flac = ['audio/x-flac']
      const wav = ['audio/wav', 'audio/x-wav']
      const mimes = [].concat(mp3, ogg, flac, wav)
      return mimes.join(',')
    },
    licenceChoices () {
      return [
        { value: 0, text: 'Not Specified' },
        { value: 1, text: 'CC Attribution' },
        { value: 2, text: 'CC Attribution Share Alike' },
        { value: 3, text: 'CC Attribution No Derivatives' },
        { value: 4, text: 'CC Attribution Non Commercial' },
        { value: 5, text: 'CC Attribution Non Commercial - Share Alike' },
        { value: 6, text: 'CC Attribution Non Commercial - No Derivatives' },
        { value: 7, text: 'Public Domain Dedication' },
        { value: 99, text: 'Other, see description' }
      ]
    },
    ...mapState({
      signedIn: (state) => !!state.users.currentUser,
      isPending: (state) => state.tracks.uploadPending,
      serverValidationErrors: (state) => state.tracks.uploadErrors
    })
  },
  methods: {
    async upload () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('track upload: uploading')
          await this.trackUpload(this.track)
          this.$router.push({ name: 'tracks-show', id: 0 })
        } catch (error) {
          console.warn('Upload failed: ' + error)
        }
      } else {
        console.log('form is invalid', this.$v.$invalid)
      }
    },
    uploadFile (event) {
      // TODO check if in case of file to big, the upload isn't submitted
      const file = event.target.files[0]
      if (!file) { return }
      if (file.size > this.$store.state.instance.track_size_limit) {
        const filesize = fileSizeFormatService.fileSizeFormat(file.size)
        const allowedSize = fileSizeFormatService.fileSizeFormat(this.$store.state.instance.track_size_limit)
        this.trackUploadError = 'file too big: ' + filesize.num + filesize.unit + '/' + allowedSize.num + allowedSize.unit
        return
      }
      this.track.file = file
      this.$v.track.file.$touch()
    }
  }
}
</script>
