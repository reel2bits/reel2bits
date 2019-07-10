<template>
  <div>
    <h4>Show track</h4>
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
    processing_done: null
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
      } catch (e) {
        this.errors = e.message
      }
    }
  }
}
</script>
