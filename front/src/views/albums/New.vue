<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <h4>Create a new album</h4>
      <b-form class="albums-new-form" @submit.prevent="create(album)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.album.title.$error }"
          label="Title:"
          label-for="title"
        >
          <b-form-input
            id="title"
            v-model.trim="$v.album.title.$model"
            :disabled="isPending"
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
            :disabled="isPending"
            :placeholder="descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-checkbox
          id="private"
          v-model="album.private"
          name="private"
          value="y"
          unchecked-value=""
          :disabled="isPending"
        >
          this album is private
        </b-form-checkbox>

        <br>

        <b-button :disabled="isPending" type="submit" variant="primary">
          Create
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

export default {
  mixins: [validationMixin],
  data: () => ({
    albumNewError: '',
    album: {
      title: '',
      description: '',
      private: ''
    }
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
    ...mapState({
      signedIn: state => !!state.users.currentUser,
      isPending: state => state.albums.createPending,
      serverValidationErrors: state => state.albums.createErrors
    })
  },
  methods: {
    ...mapActions(['albumNew']),
    async create () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('album create: uploading')
          await this.albumNew(this.album)
          this.$router.push({ name: 'albums-show', params: { username: this.$store.state.users.currentUser.screen_name, albumId: this.$store.state.albums.albumSlug } })
        } catch (error) {
          console.warn('Upload failed: ' + error)
        }
      } else {
        console.log('form is invalid', this.$v.$invalid)
      }
    }
  }
}
</script>
