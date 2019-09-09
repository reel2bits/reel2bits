<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <h4 v-translate translate-context="Content/AlbumNew/Headline">
        Create a new album
      </h4>
      <b-form class="albums-new-form" @submit.prevent="create(album)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.album.title.$error }"
          :label="labels.titleLabel"
          label-for="title"
        >
          <b-form-input
            id="title"
            v-model.trim="$v.album.title.$model"
            :disabled="isPending"
            :placeholder="labels.titlePlaceholder"
            :state="$v.album.title.$dirty ? !$v.album.title.$error : null"
            aria-describedby="title-live-feedback"
          />
          <b-form-invalid-feedback id="title-live-feedback">
            <span v-if="!$v.album.title.required" v-translate translate-context="Content/AlbumNew/Feedback/Title/Required">A title is required</span>
            <span v-if="!$v.album.title.maxLength" v-translate translate-context="Content/AlbumNew/Feedback/Title/LengthLimit">Length is limited to 250 characters</span>
          </b-form-invalid-feedback>
        </b-form-group>

        <b-form-group
          id="ig-description"
          :label="labels.descriptionLabel"
          label-for="description"
        >
          <b-form-textarea
            id="description"
            v-model="album.description"
            :disabled="isPending"
            :placeholder="labels.descriptionPlaceholder"
          />
        </b-form-group>

        <b-form-checkbox
          id="private"
          v-model="album.private"
          v-translate
          name="private"
          value="y"
          unchecked-value=""
          :disabled="isPending"
          translate-context="Content/AlbumNew/Input.Label/Private album"
        >
          this album is private
        </b-form-checkbox>

        <br>

        <b-button v-translate :disabled="isPending" type="submit"
                  variant="primary" translate-context="Content/AlbumNew/Button/Create"
        >
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
    ...mapState({
      signedIn: state => !!state.users.currentUser,
      isPending: state => state.albums.createPending,
      serverValidationErrors: state => state.albums.createErrors
    }),
    labels () {
      return {
        titleLabel: this.$pgettext('Content/AlbumNew/Input.Label/Email', 'Title:'),
        titlePlaceholder: this.$pgettext('Content/AlbumNew/Input.Placeholder/Title', 'Your album title.'),
        descriptionLabel: this.$pgettext('Content/AlbumNew/Input.Label/Description', 'Description:'),
        descriptionPlaceholder: this.$pgettext('Content/AlbumNew/Input.Placeholder/Description', 'Optional, what is this album about ?')
      }
    }
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
