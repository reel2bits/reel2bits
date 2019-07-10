<template>
  <div>
    <h4>Show track</h4>
    <div v-if="errors">
      {{ errors }}
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
    },
    userName () {
      return this.$route.params.username
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
      } catch (e) {
        this.errors = e.message
      }
    }
  }
}
</script>
