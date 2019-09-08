<template>
  <div v-if="albumError || !album" class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="albumError" variant="danger" show>
        {{ albumError }}
      </b-alert>
    </div>
  </div>
  <div v-else class="row">
    <div class="col-md-8">
      <b-alert v-if="deleteError" variant="danger" show
               dismissible
               @dismissed="deleteError=null"
      >
        {{ deleteError }}
      </b-alert>

      <h4>Show album</h4>
      <div class="btn-group" role="group" aria-label="Albums actions">
        <div v-if="isOwner">
          <b-button variant="link" class="text-decoration-none"
                    @click.prevent="editAlbum"
          >
            <i class="fa fa-pencil" aria-hidden="true" /> Edit
          </b-button>
          <b-button v-b-modal.modal-delete variant="link"
                    class="text-decoration-none"
          >
            <i class="fa fa-times" aria-hidden="true" /> Delete
          </b-button>
          <b-modal id="modal-delete" title="Deleting album" @ok="deleteAlbum">
            <p class="my-4">
              Are you sure you want to delete '{{ album.title }}' ?
            </p>
          </b-modal>
        </div>
      </div>

      <div>
        Album: {{ album }}
      </div>
    </div>

    <div v-if="album" class="col-md-4 d-flex flex-column">
      <!-- Profile Card -->
      <UserCard :user="album.account" />
      <!-- Footer -->
      <Footer />
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import moment from 'moment'
import UserCard from '../../components/user_card/user_card.vue'
import Footer from '../../components/footer/footer.vue'

export default {
  components: {
    UserCard,
    Footer
  },
  data: () => ({
    album: null,
    albumError: null,
    deleteError: null,
    isOwner: false,
    userId: null
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    albumId () {
      return this.$route.params.albumId
    },
    userName () {
      return this.$route.params.username
    },
    publishedAgo () {
      return moment(this.album.uploaded_on).fromNow()
    }
  },
  created () {
    const user = this.$store.getters.findUser(this.userName)
    if (user) {
      this.userId = user.id
    } // else, oops
    this.fetchAlbum()
  },
  methods: {
    async fetchAlbum () {
      // || quick fix before we fully implement id or username thing
      await this.$store.state.api.backendInteractor.albumFetch({ userId: this.userId || this.userName, albumId: this.albumId })
        .then((data) => {
          this.album = data
          this.isOwner = (this.album.account.screen_name === this.$store.state.users.currentUser.screen_name)
        })
    },
    async editAlbum () {
      if (!this.isOwner) { return }
      console.log('want to edit album')
      this.$router.push({ name: 'albums-edit', params: { userId: this.album.account.id, albumId: this.album.slug } })
    },
    async deleteAlbum () {
      if (!this.isOwner) { return }
      console.log('deleting album')
      try {
        await this.$store.state.api.backendInteractor.albumDelete({ userId: this.album.account.id, albumId: this.albumId })
      } catch (e) {
        console.log('an error occured')
        console.log(e)
        this.deleteError = 'an error occured while deleting the album.'
        return
      }
      this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
    }
  }
}
</script>
