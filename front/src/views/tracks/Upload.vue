<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4>Upload a new track</h4>
      <b-form class="upload-track-form" enctype="multipart/form-data" @submit.prevent="upload(track)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.track.title.$error }"
          label="Title:"
          label-for="title"
          description="If no title provided, the filename will be used."
        >
          <b-form-input
            id="title"
            v-model.trim="$v.track.title.$model"
            :disabled="isPending"
            placeholder="title"
            :state="$v.track.title.$dirty ? !$v.track.title.$error : null"
            aria-describedby="title-live-feedback"
          />
          <b-form-invalid-feedback id="title-live-feedback">
            <span v-if="!$v.track.title.maxLength">Length is limited to 250 characters</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-description"
          label="Description:"
          label-for="description"
        >
          <b-form-textarea
            id="description"
            v-model="track.description"
            :disabled="isPending"
            :placeholder="descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-group
          id="ig-file"
          label="Track file:"
          label-for="file"
        >
          <b-form-file
            :accept="acceptedMimeTypes"
            name="file"
            :disabled="isPending"
            required
            @change="uploadFile($event)"
          />
        </b-form-group>

        <b-form-group
          id="ig-album"
          label="Album:"
          label-for="album"
        >
          <b-form-select
            id="album"
            v-model="track.album"
            :disabled="isPending"
            :options="albumChoices"
          />
        </b-form-group>

        <b-form-group
          id="ig-license"
          label="License:"
          label-for="license"
        >
          <b-form-select
            id="license"
            v-model="track.licence"
            :disabled="isPending"
            :options="licenceChoices"
          />
        </b-form-group>

        <b-form-group
          id="ig-private"
          label-for="private"
          description="A private track won't federate. You can use this as your unpublished drafts. Note that you can't replace audio file after upload."
        >
          <b-form-checkbox
            id="private"
            v-model="track.private"
            name="private"
            value="y"
            unchecked-value=""
            :disabled="isPending"
          >
            this track is private
          </b-form-checkbox>
        </b-form-group>

        <br>

        <b-button :disabled="isPending" type="submit" variant="primary">
          Upload
        </b-button>

        <br>

        <b-alert v-if="serverValidationErrors.length > 0" variant="danger" show>
          <span v-for="error in serverValidationErrors" :key="error">{{ error }}</span>
        </b-alert>
      </b-form>
    </div>
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
    fetchErrors: [],
    track: {
      title: '',
      description: '',
      file: '',
      album: '__None',
      licence: 0,
      private: ''
    },
    licenceChoices: [],
    albumChoices: []
  }),
  validations: {
    track: {
      title: { maxLength: maxLength(250) },
      description: {},
      file: { required },
      album: { required },
      licence: { required },
      private: {}
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
    albumsList () {
      return [{ value: '__None', text: 'No album' }]
    },
    ...mapState({
      signedIn: state => !!state.users.currentUser,
      isPending: state => state.tracks.uploadPending,
      serverValidationErrors: state => state.tracks.uploadErrors
    })
  },
  created () {
    // Fetch licenses
    this.$store.state.api.backendInteractor.fetchLicenses()
      .then((licenses) => {
        this.licenceChoices = licenses.map(function (x) { return { value: x.id, text: x.name } })
      })
      .catch((e) => {
        console.log('error fetching licenses: ' + e)
        this.fetchErrors += 'Error fetching licenses'
        this.licenceChoices = []
      })
    // Fetch user albums
    this.$store.state.api.backendInteractor.fetchUserAlbums({ username: this.$store.state.users.currentUser.screen_name, short: true })
      .then((albums) => {
        let noAlbum = [
          { value: '__None', text: 'No album' }
        ]
        let userAlbums = albums.map(function (x) { return { value: x.id, text: (x.private ? `${x.title} (private)` : x.title) } })
        this.albumChoices = noAlbum.concat(userAlbums)
      })
      .catch((e) => {
        console.log('error fetching user albums: ' + e)
        this.fetchErrors += 'Error fetching albums'
        this.albumChoices = []
      })
  },
  methods: {
    ...mapActions(['uploadTrack']),
    async upload () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('track upload: uploading')
          await this.uploadTrack(this.track)
          this.$router.push({ name: 'tracks-show', params: { username: this.$store.state.users.currentUser.screen_name, trackId: this.$store.state.tracks.uploadSlug } })
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
      if (!file) {
        return
      }
      if (file.size > this.$store.state.instance.trackSizeLimit) {
        const filesize = fileSizeFormatService.fileSizeFormat(file.size)
        const allowedSize = fileSizeFormatService.fileSizeFormat(
          this.$store.state.instance.trackSizeLimit
        )
        this.trackUploadError =
          'file too big: ' +
          filesize.num +
          filesize.unit +
          '/' +
          allowedSize.num +
          allowedSize.unit
        return
      }
      this.track.file = file
      this.$v.track.file.$touch()
    }
  }
}
</script>
