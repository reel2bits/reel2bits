<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4>Edit album</h4>
      <b-form class="edit-album-form" enctype="multipart/form-data" @submit.prevent="edit(album)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.album.title.$error }"
          label="Title:"
          label-for="title"
        >
          <b-form-input
            id="title"
            v-model.trim="$v.album.title.$model"
            placeholder="title"
            :state="$v.album.title.$dirty ? !$v.album.title.$error : null"
            aria-describedby="title-live-feedback"
          />
          <b-form-invalid-feedback id="title-live-feedback">
            <span v-if="!$v.album.title.required">A title is required</span>
            <span v-if="!$v.album.title.maxLength">Length is limited to 250 characters</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-description"
          label="Description:"
          label-for="description"
        >
          <b-form-textarea
            id="description"
            v-model="album.description"
            :placeholder="descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-checkbox
          v-if="!alreadyFederated"
          id="private"
          v-model="album.private"
          name="private"
          value="y"
          unchecked-value=""
        >
          this album is private
        </b-form-checkbox>

        <br>

        <b-button type="submit" variant="primary">
          Edit
        </b-button>

        <b-button variant="warning" :to="{ name: 'albums-show', params: { username: userName, albumId: albumId } }">
          Cancel
        </b-button>

        <br>

        <b-alert v-if="albumEditError" variant="danger" show>
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
    albumEditError: '',
    fetchErrors: [],
    album: {
      title: '',
      description: '',
      private: ''
    },
    albumObj: null,
    alreadyFederated: null
  }),
  validations: {
    album: {
      title: { required, maxLength: maxLength(250) },
      description: {},
      private: {}
    }
  },
  computed: {
    descriptionPlaceholder () {
      return 'Optional, what is this album about ?'
    },
    albumId () {
      return this.$route.params.albumId
    },
    userName () {
      return this.$route.params.username
    },
    ...mapState({
      signedIn: state => !!state.users.currentUser
    })
  },
  async created () {
    this.fetchAlbum()
  },
  methods: {
    async fetchAlbum () {
      console.log('fetching album...')
      await this.$store.state.api.backendInteractor.albumFetch({ userId: this.userName, albumId: this.albumId })
        .then((album) => {
          this.album.title = album.title
          this.album.description = unescape(album.description)
          this.album.private = album.private
          this.alreadyFederated = !this.album.private
          this.albumObj = album
          console.log('album fetched')
        })
        .catch((e) => {
          console.log('cannot fetch album:' + e.message)
          this.albumError = e
        })
    },
    async edit () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('album editing')
          await this.$store.state.api.backendInteractor.albumEdit({ username: this.$store.state.users.currentUser.screen_name, albumId: this.albumObj.slug, album: this.album })
            .then((album) => {
              // If name change, slug change
              this.$router.push({ name: 'albums-show', params: { username: this.$store.state.users.currentUser.screen_name, albumId: album.slug } })
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
