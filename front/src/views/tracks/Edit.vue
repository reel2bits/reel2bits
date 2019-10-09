<template>
  <div>
    <div class="row justify-content-md-center">
      <div class="col-md-5">
        <b-alert v-if="fetchErrors.length > 0" variant="danger" show
                 dismissible
                 @dismissed="fetchErrors=[]"
        >
          <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
        </b-alert>

        <h4 v-translate translate-context="Content/TrackEdit/Headline" class="text-center">
          Edit track
        </h4>
      </div>
    </div>

    <b-form class="edit-track-form" enctype="multipart/form-data" @submit.prevent="edit(track)">
      <div class="row justify-content-md-center">
        <div class="col-md-5">
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
            id="ig-genre"
            :class="{ 'form-group--error': $v.track.genre.$error }"
            :label="labels.genreLabel"
            label-for="genre"
          >
            <vue-simple-suggest
              v-model="$v.track.genre.$model"
              :list="getGenres"
              :filter-by-query="true"
              :styles="autoCompleteStyle"
              :destyled="true"
              :min-length="genresAutoComplete.minLength"
              :max-suggestions="genresAutoComplete.maxSuggestions"
            />

            <b-form-invalid-feedback id="genre-live-feedback">
              <span v-if="!$v.track.genre.maxLength" v-translate translate-context="Content/TrackUpload/Feedback/Genre/LengthLimit">Length is limited to 250 characters</span>
            </b-form-invalid-feedback>
          </b-form-group>

          <b-form-group
            id="ig-tags"
            :class="{ 'form-group--error': false }"
            :label="labels.tagLabel"
            label-for="tag"
          >
            <vue-tags-input
              v-model="curTag"
              :tags="track.tags"
              :autocomplete-items="autocompleteTags"
              :add-only-from-autocomplete="false"
              :allow-edit-tags="true"
              :max-tags="10"
              :validation="tagsValidations"
              :maxlength="25"
              @tags-changed="updateTags"
            />
          </b-form-group>
        </div>

        <div class="col-md-5">
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
        </div>
      </div>
    </b-form>

    <hr>

    <div class="row justify-content-md-center">
      <div class="col-sm-4">
        <p v-translate translate-context="Content/TrackEdit/Text/Artwork picker" class="visibility-notice">
          The recommended minimum size for artworks pictures is 112x112 pixels. JPEG, PNG or GIF only.
        </p>
        <p v-translate translate-context="Content/TrackEdit/Title/Artwork picker">
          Current artwork
        </p>
        <img
          :src="currentArtwork"
          class="current-artwork"
          width="112"
          height="112"
        >
      </div>
      <div class="col-sm-4">
        <p v-translate translate-context="Content/TrackEdit/Title/Artwork picker">
          Set new artwork
        </p>
        <b-button
          v-show="pickArtworkBtnVisible"
          id="pick-artwork"
        >
          <translate translate-context="Content/TrackEdit/Button/Artwork picker">
            Upload an image
          </translate>
        </b-button>

        <image-cropper
          trigger="#pick-artwork"
          :submit-handler="submitArtwork"
          @open="pickArtworkBtnVisible=false"
          @close="pickArtworkBtnVisible=true"
        />
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.z-1000 {
  z-index: 1000;
}
.hover {
  background-color: #007bff;
  color: #fff;
}
</style>

<script>
import { validationMixin } from 'vuelidate'
import { required, maxLength } from 'vuelidate/lib/validators'
import { mapState } from 'vuex'
import unescape from 'lodash/unescape'
import VueSimpleSuggest from 'vue-simple-suggest'
import VueTagsInput from '@johmun/vue-tags-input'
import ImageCropper from '../../components/image_cropper/image_cropper.vue'

export default {
  components: {
    VueSimpleSuggest,
    VueTagsInput,
    ImageCropper
  },
  mixins: [validationMixin],
  data: () => ({
    trackEditError: '',
    fetchErrors: [],
    track: {
      title: '',
      description: '',
      album: '__None',
      licence: 0,
      private: '',
      tags: []
    },
    trackObj: null,
    licenceChoices: [],
    albumChoices: [],
    alreadyFederated: null,
    autoCompleteStyle: {
      vueSimpleSuggest: 'position-relative',
      inputWrapper: '',
      defaultInput: 'form-control',
      suggestions: 'position-absolute list-group z-1000',
      suggestItem: 'list-group-item'
    },
    genresAutoComplete: {
      minLength: 3,
      maxSuggestions: 4
    },
    curTag: '',
    autocompleteTags: [],
    debounceTags: null,
    tagsValidations: [
      {
        classes: 'class',
        rule: /^([\d\w-\s]+)$/ // Allow a-Z0-9 - _(implicit by \w) and space
      }
    ],
    pickArtworkBtnVisible: true
  }),
  validations: {
    track: {
      title: { maxLength: maxLength(250) },
      description: {},
      genre: { maxLength: maxLength(250) },
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
        genreLabel: this.$pgettext('Content/TrackUpload/Input.Label/Genre', 'Genre:'),
        tagLabel: this.$pgettext('Content/TrackUpload/Input.Label/Tags', 'Tags:'),
        albumLabel: this.$pgettext('Content/TrackUpload/Input.Label/Album', 'Album:'),
        licenseLabel: this.$pgettext('Content/TrackUpload/Input.Label/License', 'License:'),
        privateDescription: this.$pgettext('Content/TrackUpload/Input.Label/Private', 'A private track won\'t federate. You can use this as your unpublished drafts. Note that you can\'t replace audio file after upload.')
      }
    },
    currentArtwork () {
      if (this.trackObj && this.trackObj.picture_url) {
        return this.trackObj.picture_url
      } else {
        return '/static/artwork_placeholder.svg'
      }
    }
  },
  watch: {
    'curTag': 'getTags'
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
        this.$bvToast.toast(this.$pgettext('Content/TracksEdit/Toast/Error/Message', 'Cannot fetch known licenses'), {
          title: this.$pgettext('Content/TracksEdit/Toast/Error/Title', 'Tracks'),
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
        this.$bvToast.toast(this.$pgettext('Content/TracksEdit/Toast/Error/Message', 'Cannot fetch user albums'), {
          title: this.$pgettext('Content/TracksEdit/Toast/Error/Title', 'Tracks'),
          autoHideDelay: 10000,
          appendToast: false,
          variant: 'danger'
        })
      })
    this.fetchTrack()
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      await this.$store.state.api.backendInteractor.trackFetch({ userId: this.userName, trackId: this.trackId })
        .then((track) => {
          this.track.title = track.title
          this.track.description = unescape(track.description)
          this.track.album = track.album_id ? track.album_id : '__None'
          this.track.licence = track.metadatas.licence.id
          this.track.private = track.private
          this.track.genre = track.genre
          this.track.tags = track.tags.map(a => { return { text: a, tiClasses: ['ti-valid'] } })
          this.alreadyFederated = !this.track.private
          this.trackObj = track
          console.log('track fetched')
        })
        .catch((e) => {
          console.log('cannot fetch track:' + e.message)
          this.trackError = e
          this.$bvToast.toast(this.$pgettext('Content/TracksEdit/Toast/Error/Message', 'Cannot fetch track'), {
            title: this.$pgettext('Content/TracksEdit/Toast/Error/Title', 'Tracks'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
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
          this.$bvToast.toast(this.$pgettext('Content/TracksEdit/Toast/Error/Message', 'Edit failed'), {
            title: this.$pgettext('Content/TracksEdit/Toast/Error/Title', 'Tracks'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        }
      } else {
        console.log('form is invalid', this.$v.$invalid)
      }
    },
    getGenres (query) {
      return this.$store.state.api.backendInteractor.fetchGenres({ query: query })
        .catch((e) => {
          this.$bvToast.toast(this.$pgettext('Content/TracksEdit/Toast/Error/Message', 'Cannot fetch genres'), {
            title: this.$pgettext('Content/TracksEdit/Toast/Error/Title', 'Genres'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        })
    },
    updateTags (newTags) {
      this.autocompleteTags = []
      this.track.tags = newTags
    },
    getTags () {
      if (this.curTag.length < 2) {
        return
      }
      clearTimeout(this.debounceTags)
      this.debounce = setTimeout(() => {
        this.$store.state.api.backendInteractor.fetchTags({ query: this.curTag })
          .then((res) => {
            this.autocompleteTags = res.map(a => { return { text: a } })
          })
          .catch((e) => {
            this.$bvToast.toast(this.$pgettext('Content/TracksUpload/Toast/Error/Message', 'Cannot fetch tags'), {
              title: this.$pgettext('Content/TracksUpload/Toast/Error/Title', 'Tags'),
              autoHideDelay: 10000,
              appendToast: false,
              variant: 'danger'
            })
          })
      }, 600)
    },
    submitArtwork (cropper, file) {
      const that = this
      return new Promise((resolve, reject) => {
        function updateArtwork (picture) {
          that.$store.state.api.backendInteractor.updateArtwork({ kind: 'track', objId: that.trackObj.slug, userId: that.$store.state.users.currentUser.screen_name, picture })
            .then((res) => {
              that.$router.push({ name: 'tracks-show', params: { username: that.$store.state.users.currentUser.screen_name, trackId: that.trackObj.slug } })
            })
            .catch((err) => {
              reject(new Error(that.$pgettext('Content/TrackEdit/Error/Message', 'cannot upload artwork: ') + err.message))
            })
        }

        if (cropper) {
          cropper.getCroppedCanvas().toBlob(updateArtwork, file.type)
        } else {
          updateArtwork(file)
        }
      })
    }
  }
}
</script>
