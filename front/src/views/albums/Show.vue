<template>
  <div>
    <h4>Show album</h4>
    <div v-if="isOwner">
      <a href="#" @click.prevent="editAlbum">edit</a> | <a href="#" @click.prevent="deleteAlbum">delete</a>
    </div>

    <div v-if="errors">
      {{ errors }}
    </div>
    <div>
      Album to show: {{ album }}
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'

export default {
  data: () => ({
    album: null,
    errors: null,
    processing_done: null,
    isOwner: false
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
    processingDone () {
      return (this.processing_done && this.album)
    }
  },
  created () {
    this.fetchAlbum()
  },
  methods: {
    async fetchAlbum () {
      try {
        let data = await apiService.albumFetch(this.userName, this.albumId, this.$store)
        this.album = data
        this.isOwner = (this.album.user === this.$store.state.users.currentUser.screen_name)
      } catch (e) {
        this.errors = e.message
      }
    },
    async editAlbum () {
      console.log('want to edit album')
    },
    async deleteAlbum () {
      console.log('want to delete album')
      if (confirm('Are you sure ?')) {
        apiService.albumDelete(this.userName, this.albumId, this.$store)
          .then(this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
          )
      }
    }
  }
}
</script>
