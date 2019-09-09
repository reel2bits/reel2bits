<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4 v-translate translate-context="Content/TrackEdit/Headline">
        Edit track
      </h4>
      <b-form class="edit-track-form" enctype="multipart/form-data" @submit.prevent="edit(track)">
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
            :placeholder="labels.titlePlaceholder"
            :state="$v.track.title.$dirty ? !$v.track.title.$error : null"
            aria-describedby="title-live-feedback"
          />
          <b-form-invalid-feedback id="title-live-feedback">
            <span v-if="!$v.track.title.maxLength" v-translate translate-context="Content/TrackEdit/Feedback/Title/LengthLimit">Length is limited to 250 characters</span>
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
            :placeholder="labels.descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-group
          id="ig-album"
          :label="labels.albumLabel"
          label-for="album"
        >
          <b-form-select
            id="album"
            v-model="track.album"
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
            :options="licenceChoices"
          />
        </b-form-group>

        <b-form-checkbox
          v-if="!alreadyFederated"
          id="private"
          v-model="track.private"
          v-translate
          name="private"
          value="y"
          unchecked-value=""
          translate-context="Content/TrackEdit/Input.Label/Private track"
        >
          this track is private
        </b-form-checkbox>

        <br>

        <b-button v-translate type="submit" variant="primary"
                  translate-context="Content/TrackEdit/Button/Edit"
        >
          Edit
        </b-button>

        <b-button v-translate variant="warning" :to="{ name: 'tracks-show', params: { username: userName, trackId: trackId } }"
                  translate-context="Content/TrackEdit/Button/Cancel"
        >
          Cancel
        </b-button>

        <br>

        <b-alert v-if="trackEditError" variant="danger" show>
          <span>{{ error }}</span>
        </b-alert>
      </b-form>
    </div>
  </div>
</template>

<script>
import { validationMixin } from 'vuelidate'
import { required, maxLength } from 'vuelidate/lib/validators'
import { mapState } from 'vuex'
import unescape from 'lodash/unescape'

export default {
  mixins: [validationMixin],
  data: () => ({
    trackEditError: '',
    fetchErrors: [],
    track: {
      title: '',
      description: '',
      album: '__None',
      licence: 0,
      private: ''
    },
    trackObj: null,
    licenceChoices: [],
    albumChoices: [],
    alreadyFederated: null
  }),
  validations: {
    track: {
      title: { maxLength: maxLength(250) },
      description: {},
      album: { required },
      licence: { required },
      private: {}
    }
  },
  computed: {
    trackId () {
      return this.$route.params.trackId
    },
    userName () {
      return this.$route.params.username
    },
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    labels () {
      return {
        titleLabel: this.$pgettext('Content/TrackUpload/Input.Label/Email', 'Title:'),
        titleDescription: this.$pgettext('Content/TrackUpload/Input.Label/Title', 'If no title provided, the filename will be used.'),
        titlePlaceholder: this.$pgettext('Content/TrackUpload/Input.Placeholder/Title', 'Your track title.'),
        descriptionLabel: this.$pgettext('Content/TrackUpload/Input.Label/Description', 'Description:'),
        descriptionPlaceholder: this.$pgettext('Content/TrackUpload/Input.Placeholder/Description', 'Optional, what is this track about ?'),
        albumLabel: this.$pgettext('Content/TrackUpload/Input.Label/Album', 'Album:'),
        licenseLabel: this.$pgettext('Content/TrackUpload/Input.Label/License', 'License:'),
        privateDescription: this.$pgettext('Content/TrackUpload/Input.Label/Private', 'A private track won\'t federate. You can use this as your unpublished drafts. Note that you can\'t replace audio file after upload.')
      }
    }
  },
  async created () {
    // Fetch licenses
    this.$store.state.api.backendInteractor.fetchLicenses()
      .then((licenses) => {
        this.licenceChoices = licenses.map(function (x) { return { value: x.id, text: x.name } })
      })
      .catch((e) => {
        console.log('error fetching licenses: ' + e)
        this.fetchErrors += this.$pgettext('Content/TrackUpload/Error', 'Error fetching licenses')
        this.licenceChoices = []
      })
    // Fetch user albums
    this.$store.state.api.backendInteractor.fetchUserAlbums({ userId: this.$store.state.users.currentUser.userId, short: true })
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
      })
    this.fetchTrack()
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      await this.$store.state.api.backendInteractor.trackFetch({ user: this.userName, trackId: this.trackId })
        .then((track) => {
          this.track.title = track.title
          this.track.description = unescape(track.description)
          this.track.album = track.album_id ? track.album_id : '__None'
          this.track.licence = track.metadatas.licence.id
          this.track.private = track.private
          this.alreadyFederated = !this.track.private
          this.trackObj = track
          console.log('track fetched')
        })
        .catch((e) => {
          console.log('cannot fetch track:' + e.message)
          this.trackError = e
        })
    },
    async edit () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('track editing')
          await this.$store.state.api.backendInteractor.trackEdit({ username: this.$store.state.users.currentUser.screen_name, trackId: this.trackObj.slug, track: this.track })
            .then((track) => {
              // If name change, slug change
              this.$router.push({ name: 'tracks-show', params: { username: this.$store.state.users.currentUser.screen_name, trackId: track.slug } })
            })
        } catch (error) {
          console.warn('Edit failed: ' + error)
        }
      } else {
        console.log('form is invalid', this.$v.$invalid)
      }
    }
  }
}
</script>
