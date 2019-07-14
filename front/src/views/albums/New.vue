<template>
  <div>
    <h4>Create a new album</h4>
    <form class="albums-new-form" @submit.prevent="create(album)">
      <div class="container">
        <div class="text-fields">
          <div class="form-group" :class="{ 'form-group--error': $v.album.title.$error }">
            <label class="form--label" for="album-new-title">title</label>
            <input id="album-new-title" v-model.trim="$v.album.title.$model" :disabled="isPending"
                   class="form-control" placeholder="title"
            >
          </div>

          <div class="form-group">
            <label class="form--label" for="description">description</label>
            <textarea id="description" v-model="album.description" :disabled="isPending"
                      class="form-control" :placeholder="descriptionPlaceholder"
            />
          </div>

          <div class="form-group">
            <label class="form--label" for="private">private</label>
            <input id="private" v-model="album.private" type="checkbox"
                   name="private" value="y" :disabled="isPending"
                   class="form-control"
            >
          </div>

          <div class="form-group">
            <button :disabled="isPending" type="submit" class="btn btn-default">
              upload
            </button>
          </div>
        </div>
      </div>
      <div v-if="serverValidationErrors.length" class="form-group">
        <div class="alert error">
          <span v-for="error in serverValidationErrors" :key="error">{{ error }}</span>
        </div>
      </div>
    </form>
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
  created () {
    console.log('album new created() called')
    if (!this.signedIn) {
      console.debug('not logged in, redirecting')
      this.$router.push({ name: 'home' })
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
