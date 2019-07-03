<template>
  <div>
    <h4>Upload a new track</h4>
    <form
      class="upload-track-form"
      enctype="multipart/form-data"
      @submit.prevent="upload(track)"
    >
      <div class="container">
        <div class="text-fields">
          <div
            class="form-group"
            :class="{ 'form-group--error': $v.track.title.$error }"
          >
            <label
              class="form--label"
              for="track-upload-title"
            >title</label>
            <input
              id="track-upload-title"
              v-model.trim="$v.track.title.$model"
              :disabled="isPending"
              class="form-control"
              placeholder="title"
            >
          </div>

          <div class="form-group">
            <label
              class="form--label"
              for="description"
            >description</label>
            <textarea
              id="description"
              v-model="track.description"
              :disabled="isPending"
              class="form-control"
              :placeholder="descriptionPlaceholder"
            />
          </div>

          <div class="form-group">
            <label
              class="form--label"
              for="file"
            >file</label>
            <input
              id="file"
              :accept="acceptedMimeTypes"
              type="file"
              name="file"
              required=""
              :disabled="isPending"
              class="form-control-file"
              @change="uploadFile($event)"
            >
          </div>
          <div
            v-if="$v.track.file.$dirty"
            class="form-error"
          >
            <ul>
              <li v-if="!$v.track.file.required">
                <span>file required</span>
              </li>
            </ul>
          </div>
          <div
            v-if="trackUploadError"
            class="form-error"
          >
            Error: {{ trackUploadError }}
          </div>

          <!-- TODO: album -->

          <div class="form-group">
            <label
              class="form--label"
              for="licence"
            >licence</label>
            <select
              id="licence"
              v-model="track.licence"
              class="form-control"
              name="licence"
            >
              <option
                v-for="lic in licenceChoices"
                :key="lic.value"
                :value="lic.value"
              >
                {{ lic.text }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label
              class="form--label"
              for="private"
            >private</label>
            <input
              id="private"
              v-model="track.private"
              type="checkbox"
              name="private"
              value="y"
              :disabled="isPending"
              class="form-control"
            >
          </div>

          <div class="form-group">
            <button
              :disabled="isPending"
              type="submit"
              class="btn btn-default"
            >
              upload
            </button>
          </div>
        </div>
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
import { required, maxLength } from 'vuelidate/lib/validators'
import { mapState, mapActions } from 'vuex'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'

export default {
  mixins: [validationMixin],
  data: () => ({
    trackUploadError: '',
    track: {
      title: '',
      description: '',
      file: '',
      album: null,
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
  computed: {
    descriptionPlaceholder () {
      return 'Optional, what is this track about ?'
    },
    acceptedMimeTypes () {
      const exts = ['.mp3', '.ogg', '.oga', '.flac', '.wav']
      const mp3 = ['audio/mpeg3', 'audio/x-mpeg-3']
      const ogg = ['audio/ogg', 'audio/x-ogg']
      const flac = ['audio/x-flac']
      const wav = ['audio/wav', 'audio/x-wav']
      const mimes = [].concat(exts, mp3, ogg, flac, wav)
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
  created () {
    console.log('upload view created() called')
    if (!this.signedIn) {
      console.debug('not logged in, redirecting')
      this.$router.push({ name: 'home' })
    }
  },
  methods: {
    ...mapActions(['uploadTrack']),
    async upload () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('track upload: uploading')
          await this.uploadTrack(this.track)
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
