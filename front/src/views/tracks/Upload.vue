<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4 v-translate translate-context="Content/TrackUpload/Headline">
        Upload a new track
      </h4>

      <template v-if="currentUser.reel2bits.quota_limit > 0">
        <b-alert show :variant="currentUserQuotaLevel">
          {{ currentUserQuota }}
        </b-alert>
      </template>

      <b-form class="upload-track-form" enctype="multipart/form-data" @submit.prevent="upload(track)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.track.title.$error }"
          :label="labels.titleLabel"
          label-for="title"
          :description="labels.titleDescription"
        >
          <b-form-input
            id="title"
            v-model.trim="$v.track.title.$model"
            :disabled="isPending"
            :placeholder="labels.titlePlaceholder"
            :state="$v.track.title.$dirty ? !$v.track.title.$error : null"
            aria-describedby="title-live-feedback"
          />
          <b-form-invalid-feedback id="title-live-feedback">
            <span v-if="!$v.track.title.maxLength" v-translate translate-context="Content/TrackUpload/Feedback/Title/LengthLimit">Length is limited to 250 characters</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-description"
          :label="labels.descriptionLabel"
          label-for="description"
        >
          <b-form-textarea
            id="description"
            v-model="track.description"
            :disabled="isPending"
            :placeholder="labels.descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-group
          id="ig-file"
          :description="fileDescription"
          :label="labels.fileLabel"
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

        <template v-if="trackUploadError">
          <br>
          <b-alert v-if="trackUploadError" variant="danger" show>
            {{ trackUploadError }}
          </b-alert>
          <br>
        </template>

        <b-form-group
          id="ig-album"
          :label="labels.albumLabel"
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
          :label="labels.licenseLabel"
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
          :description="labels.privateDescription"
        >
          <b-form-checkbox
            id="private"
            v-model="track.private"
            v-translate
            name="private"
            value="y"
            unchecked-value=""
            :disabled="isPending" translate-context="Content/TrackUpload/Input.Label/Private track"
          >
            this track is private
          </b-form-checkbox>
        </b-form-group>

        <br>

        <b-button v-translate :disabled="isPending" type="submit"
                  variant="primary" translate-context="Content/TrackUpload/Button/Upload"
        >
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
    albumChoices: [],
    currentUserQuotaLevel: 'info'
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
      serverValidationErrors: state => state.tracks.uploadErrors,
      currentUser: state => state.users.currentUser
    }),
    labels () {
      return {
        titleLabel: this.$pgettext('Content/TrackUpload/Input.Label/Email', 'Title:'),
        titleDescription: this.$pgettext('Content/TrackUpload/Input.Label/Title', 'If no title provided, the filename will be used.'),
        titlePlaceholder: this.$pgettext('Content/TrackUpload/Input.Placeholder/Title', 'Your track title.'),
        descriptionLabel: this.$pgettext('Content/TrackUpload/Input.Label/Description', 'Description:'),
        descriptionPlaceholder: this.$pgettext('Content/TrackUpload/Input.Placeholder/Description', 'Optional, what is this track about ?'),
        fileLabel: this.$pgettext('Content/TrackUpload/Input.Label/File', 'Track file:'),
        albumLabel: this.$pgettext('Content/TrackUpload/Input.Label/Album', 'Album:'),
        licenseLabel: this.$pgettext('Content/TrackUpload/Input.Label/License', 'License:'),
        privateDescription: this.$pgettext('Content/TrackUpload/Input.Label/Private', 'A private track won\'t federate. You can use this as your unpublished drafts. Note that you can\'t replace audio file after upload.')
      }
    },
    fileDescription () {
      if (this.track.file) {
        const file = event.target.files[0]

        let msg = this.$pgettext('Content/TrackUpload/File.Description', 'Maximum file size: %{maxSize}, current file: %{curSize}')
        let ffsMax = fileSizeFormatService.fileSizeFormat(this.$store.state.instance.trackSizeLimit)
        let ffsCur = fileSizeFormatService.fileSizeFormat(file.size)
        return this.$gettextInterpolate(msg, { maxSize: ffsMax.num + ffsMax.unit, curSize: ffsCur.num + ffsCur.unit })
      }
      let msg = this.$pgettext('Content/TrackUpload/File.Description', 'Maximum file size: %{maxSize}')
      let ffs = fileSizeFormatService.fileSizeFormat(this.$store.state.instance.trackSizeLimit)
      return this.$gettextInterpolate(msg, { maxSize: ffs.num + ffs.unit })
    },
    currentUserQuota () {
      if (this.currentUser.reel2bits.quota_limit > 0) {
        let max = fileSizeFormatService.fileSizeFormat(this.currentUser.reel2bits.quota_limit)
        let msg = this.$pgettext('Content/TrackUpload/Alert/Quota', 'Current quota: %{cur} of %{max}. %{rem} remaining.')
        let cur = fileSizeFormatService.fileSizeFormat(this.currentUser.reel2bits.quota_count)
        let rem = fileSizeFormatService.fileSizeFormat(this.currentUser.reel2bits.quota_limit - this.currentUser.reel2bits.quota_count)
        return this.$gettextInterpolate(msg, { max: max.num + ' ' + max.unit, cur: cur.num + ' ' + cur.unit, rem: rem.num + ' ' + rem.unit })
      }
      return null
    }
  },
  created () {
    // Fetch licenses
    this.$store.state.api.backendInteractor.fetchLicenses()
      .then((licenses) => {
        this.licenceChoices = licenses.map(function (x) { return { value: x.id, text: x.name } })
      })
      .catch((e) => {
        console.log('error fetching licenses: ' + e)
        this.fetchErrors += this.$pgettext('Content/TrackUpload/Error', 'Error fetching licenses')
        this.licenceChoices = []
        this.$bvToast.toast(this.$pgettext('Content/TracksUpload/Toast/Error/Message', 'Cannot fetch known licenses'), {
          title: this.$pgettext('Content/TracksUpload/Toast/Error/Title', 'Tracks'),
          autoHideDelay: 10000,
          appendToast: false,
          variant: 'danger'
        })
      })
    // Fetch user albums
    this.$store.state.api.backendInteractor.fetchUserAlbums({ userId: this.$store.state.users.currentUser.id, short: true })
      .then((albums) => {
        let noAlbum = [
          { value: '__None', text: 'No album' }
        ]
        let userAlbums = albums.map(function (x) { return { value: x.id, text: (x.private ? `${x.title} (private)` : x.title) } })
        this.albumChoices = noAlbum.concat(userAlbums)
      })
      .catch((e) => {
        console.log('error fetching user albums: ' + e)
        this.fetchErrors += this.$pgettext('Content/TrackUpload/Error', 'Error fetching albums')
        this.albumChoices = []
        this.$bvToast.toast(this.$pgettext('Content/TracksUpload/Toast/Error/Message', 'Cannot fetch user albums'), {
          title: this.$pgettext('Content/TracksUpload/Toast/Error/Title', 'Tracks'),
          autoHideDelay: 10000,
          appendToast: false,
          variant: 'danger'
        })
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
          this.$bvToast.toast(this.$pgettext('Content/TracksUpload/Toast/Error/Message', 'Upload failed'), {
            title: this.$pgettext('Content/TracksUpload/Toast/Error/Title', 'Tracks'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        }
      } else {
        console.log('form is invalid', this.$v.$invalid)
      }
    },
    uploadFile (event) {
      // TODO check if in case of file to big, the upload isn't submitted
      // file.size is in bytes
      const file = event.target.files[0]
      if (!file) {
        return
      }
      if (file.size > this.$store.state.instance.trackSizeLimit) {
        const filesize = fileSizeFormatService.fileSizeFormat(file.size)
        const allowedSize = fileSizeFormatService.fileSizeFormat(
          this.$store.state.instance.trackSizeLimit
        )
        let errMsg = this.$pgettext('Content/TrackUpload/Error', 'file too big: ')
        this.trackUploadError =
          errMsg +
          filesize.num +
          filesize.unit +
          '/' +
          allowedSize.num +
          allowedSize.unit
        return
      }

      // Compute quota
      let quotaCurrent = this.currentUser.reel2bits.quota_count
      let quotaLimit = this.currentUser.reel2bits.quota_limit

      if (quotaCurrent + file.size > quotaLimit) {
        this.currentUserQuotaLevel = 'danger'
        let errMsg = this.$pgettext('Content/TrackUpload/Error', 'File is too big for the current remaining quota')
        this.trackUploadError = errMsg
        return
      } else {
        this.currentUserQuotaLevel = 'info'
      }

      this.track.file = file
      this.trackUploadError = ''
      this.$v.track.file.$touch()
    }
  }
}
</script>
