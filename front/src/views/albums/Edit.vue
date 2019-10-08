<template>
  <div class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="fetchErrors.length > 0" variant="danger" show
               dismissible
               @dismissed="fetchErrors=[]"
      >
        <span v-for="error in fetchErrors" :key="error">{{ error }}</span>
      </b-alert>

      <h4 v-translate translate-context="Content/AlbumEdit/Headline">
        Edit album
      </h4>
      <b-form class="edit-album-form" enctype="multipart/form-data" @submit.prevent="edit(album)">
        <b-form-group
          id="ig-title"
          :class="{ 'form-group--error': $v.album.title.$error }"
          :label="labels.titleLabel"
          label-for="title"
        >
          <b-form-input
            id="title"
            v-model.trim="$v.album.title.$model"
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
            <span v-if="!$v.album.genre.maxLength" v-translate translate-context="Content/AlbumEdit/Feedback/Genre/LengthLimit">Length is limited to 250 characters</span>
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
          v-if="!alreadyFederated"
          id="private"
          v-model="album.private"
          v-translate
          name="private"
          value="y"
          unchecked-value=""
          translate-context="Content/AlbumEdit/Input.Label/Private album"
        >
          this album is private
        </b-form-checkbox>

        <br>

        <b-button v-translate type="submit" variant="primary"
                  translate-context="Content/AlbumEdit/Button/Edit"
        >
          Edit
        </b-button>

        <b-button v-translate variant="warning" :to="{ name: 'albums-show', params: { username: userName, albumId: albumId } }"
                  translate-context="Content/AlbumEdit/Link/Cancel"
        >
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

export default {
  components: {
    VueSimpleSuggest,
    VueTagsInput
  },
  mixins: [validationMixin],
  data: () => ({
    albumEditError: '',
    fetchErrors: [],
    album: {
      title: '',
      description: '',
      private: '',
      genre: '',
      tags: []
    },
    albumObj: null,
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
    albumId () {
      return this.$route.params.albumId
    },
    userName () {
      return this.$route.params.username
    },
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    labels () {
      return {
        titleLabel: this.$pgettext('Content/AlbumNew/Input.Label/Email', 'Title:'),
        titlePlaceholder: this.$pgettext('Content/AlbumNew/Input.Placeholder/Title', 'Your album title.'),
        descriptionLabel: this.$pgettext('Content/AlbumNew/Input.Label/Description', 'Description:'),
        descriptionPlaceholder: this.$pgettext('Content/AlbumNew/Input.Placeholder/Description', 'Optional, what is this album about ?'),
        genreLabel: this.$pgettext('Content/AlbumNew/Input.Label/Genre', 'Genre:'),
        tagLabel: this.$pgettext('Content/AlbumNew/Input.Label/Tags', 'Tags:')
      }
    }
  },
  watch: {
    'curTag': 'getTags'
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
          this.album.genre = album.genre
          this.album.tags = album.tags.map(a => { return { text: a, tiClasses: ['ti-valid'] } })
          this.albumObj = album
          console.log('album fetched')
        })
        .catch((e) => {
          console.log('cannot fetch album:' + e.message)
          this.albumError = e
          this.$bvToast.toast(this.$pgettext('Content/AlbumsEdit/Toast/Error/Message', 'Cannot fetch album'), {
            title: this.$pgettext('Content/AlbumsEdit/Toast/Error/Title', 'Album'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'danger'
          })
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
          this.$bvToast.toast(this.$pgettext('Content/AlbumsEdit/Toast/Error/Message', 'Edit failed'), {
            title: this.$pgettext('Content/AlbumsEdit/Toast/Error/Title', 'Album'),
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
          this.$bvToast.toast(this.$pgettext('Content/AlbumEdit/Toast/Error/Message', 'Cannot fetch genres'), {
            title: this.$pgettext('Content/AlbumEdit/Toast/Error/Title', 'Genres'),
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
            this.$bvToast.toast(this.$pgettext('Content/AlbumEdit/Toast/Error/Message', 'Cannot fetch tags'), {
              title: this.$pgettext('Content/AlbumEdit/Toast/Error/Title', 'Tags'),
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
