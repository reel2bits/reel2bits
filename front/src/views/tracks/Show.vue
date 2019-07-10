<template>
  <div>
    <h4>Show track</h4>
    <div v-if="errors">
      Errors: {{ errors }}
    </div>
    <div v-if="track">
      Track to show: {{ track }}
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'

export default {
  data: () => ({
    track: null,
    errors: null
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    trackId () {
      return this.$route.params.trackId
    }
  },
  created () {
    this.fetchTrack()
  },
  methods: {
    fetchTrack () {
      try {
        let data = apiService.trackFetch(this.trackId(), this.$store)
        this.track = data
      } catch (e) {
        this.errors = JSON.parse(e.message)
      }
    }
  }
}
</script>
