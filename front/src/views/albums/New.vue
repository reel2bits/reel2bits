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

        <b-form-group
          id="ig-genre"
          :class="{ 'form-group--error': $v.album.genre.$error }"
          :label="labels.genreLabel"
          label-for="genre"
        >
          <vue-simple-suggest
            v-model="$v.album.genre.$model"
            :list="getGenres"
            :filter-by-query="true"
            :styles="autoCompleteStyle"
            :destyled="true"
            :min-length="genresAutoComplete.minLength"
            :max-suggestions="genresAutoComplete.maxSuggestions"
          />

          <b-form-invalid-feedback id="genre-live-feedback">
            <span v-if="!$v.album.genre.maxLength" v-translate translate-context="Content/AlbumNew/Feedback/Genre/LengthLimit">Length is limited to 250 characters</span>
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
            :tags="album.tags"
            :autocomplete-items="autocompleteTags"
            :add-only-from-autocomplete="false"
            :allow-edit-tags="true"
            :max-tags="10"
            :validation="tagsValidations"
            :maxlength="25"
            @tags-changed="updateTags"
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
import { mapState, mapActions } from 'vuex'
import VueSimpleSuggest from 'vue-simple-suggest'
import VueTagsInput from '@johmun/vue-tags-input'

export default {
  components: {
    VueSimpleSuggest,
    VueTagsInput
  },
  mixins: [validationMixin],
  data: () => ({
    albumNewError: '',
    album: {
      title: '',
      description: '',
      private: '',
      genre: '',
      tags: []
    },
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
    ]
  }),
  validations: {
    album: {
      title: { required, maxLength: maxLength(250) },
      description: {},
      private: {},
      genre: { maxLength: maxLength(250) },
      tags: {}
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
        descriptionPlaceholder: this.$pgettext('Content/AlbumNew/Input.Placeholder/Description', 'Optional, what is this album about ?'),
        genreLabel: this.$pgettext('Content/TrackUpload/Input.Label/Genre', 'Genre:'),
        tagLabel: this.$pgettext('Content/TrackUpload/Input.Label/Tags', 'Tags:')
      }
    }
  },
  watch: {
    'curTag': 'getTags'
  },
  methods: {
    ...mapActions(['albumNew']),
    async create () {
      this.$v.$touch()

      if (!this.$v.$invalid) {
        try {
          console.debug('album create: saving')
          await this.albumNew(this.album)
          this.$router.push({ name: 'albums-show', params: { username: this.$store.state.users.currentUser.screen_name, albumId: this.$store.state.albums.albumSlug } })
        } catch (error) {
          console.warn('Save failed: ' + error)
          this.$bvToast.toast(this.$pgettext('Content/AlbumsNew/Toast/Error/Message', 'Cannot save album'), {
            title: this.$pgettext('Content/AlbumsNew/Toast/Error/Title', 'Album'),
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
          this.$bvToast.toast(this.$pgettext('Content/AlbumsNew/Toast/Error/Message', 'Cannot fetch genres'), {
            title: this.$pgettext('Content/AlbumsNew/Toast/Error/Title', 'Genres'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        })
    },
    updateTags (newTags) {
      this.autocompleteTags = []
      this.album.tags = newTags
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
            this.$bvToast.toast(this.$pgettext('Content/AlbumsNew/Toast/Error/Message', 'Cannot fetch tags'), {
              title: this.$pgettext('Content/AlbumsNew/Toast/Error/Title', 'Tags'),
              autoHideDelay: 10000,
              appendToast: false,
              variant: 'danger'
            })
          })
      }, 600)
    }
  }
}
</script>
