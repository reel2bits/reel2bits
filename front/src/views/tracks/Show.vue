<template>
  <div>
    <h4>Show track</h4>
    <div v-if="isOwner">
      <a href="#" @click="editTrack">edit</a> | <a href="#" @click="deleteTrack">delete</a>
    </div>

    <div v-if="errors">
      {{ errors }}
    </div>
    <div v-if="processingDone">
      Track to show: {{ track }}
    </div>
    <div v-else-if="processingDone">
      Track not yet available.
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'

export default {
  data: () => ({
    track: null,
    errors: null,
    processing_done: null,
    isOwner: false
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    trackId () {
      return this.$route.params.trackId
    },
    userName () {
      return this.$route.params.username
    },
    processingDone () {
      return (this.processing_done && this.track)
    }
  },
  created () {
    this.fetchTrack()
  },
  methods: {
    async fetchTrack () {
      try {
        let data = await apiService.trackFetch(this.userName, this.trackId, this.$store)
        this.track = data
        this.processing_done = this.track.processing.done
        this.isOwner = (this.track.user === this.$store.state.users.currentUser.screen_name)
      } catch (e) {
        this.errors = e.message
      }
    },
    async editTrack () {
      console.log('want to edit track')
    },
    async deleteTrack () {
      console.log('want to delete track')
      if (confirm('Are you sure ?')) {
        apiService.trackDelete(this.userName, this.trackId, this.$store)
          .then(this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
          )
      }
    }
  }
}
</script>
