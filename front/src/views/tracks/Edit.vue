<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4>Edit track</h4>
      <b-form class="edit-track-form" enctype="multipart/form-data" @submit.prevent="edit(track)">
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
            :placeholder="descriptionPlaceholder"
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
            :options="albumsList"
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
            :options="licenceChoices"
          />
        </b-form-group>

        <b-form-checkbox
          v-if="!alreadyFederated"
          id="private"
          v-model="track.private"
          name="private"
          value="y"
          unchecked-value=""
        >
          this track is private
        </b-form-checkbox>

        <br>

        <b-button type="submit" variant="primary">
          Edit
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
    descriptionPlaceholder () {
      return 'Optional, what is this track about ?'
    },
    albumsList () {
      return [{ value: '__None', text: 'No album' }]
    },
    trackId () {
      return this.$route.params.trackId
    },
    userName () {
      return this.$route.params.username
    },
    ...mapState({
      signedIn: state => !!state.users.currentUser
    })
  },
  created () {
    this.$store.state.api.backendInteractor.fetchLicenses()
      .then((licenses) => {
        this.licenceChoices = licenses.map(function (x) { return { value: x.id, text: x.name } })
        this.fetchTrack()
      })
      .catch((e) => {
        console.log('error fetching licenses: ' + e)
        this.fetchErrors += 'Error fetching licenses'
        this.licenceChoices = []
      })
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      await this.$store.state.api.backendInteractor.trackFetch({ user: this.userName, trackId: this.trackId })
        .then((track) => {
          this.track.title = track.title
          this.track.description = unescape(track.description)
          this.track.album = '__None'
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
