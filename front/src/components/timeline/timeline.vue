<template>
  <div v-if="timelineError" class="row justify-content-md-center">
    <div class="col-md-8">
      <p class="h3">
        {{ title }}
      </p>
      <b-alert v-if="timelineError" variant="danger" show>
        {{ timelineError }}
      </b-alert>
    </div>
  </div>
  <div v-else>
    <div class="row">
      <div class="col-md-8">
        <p class="h3">
          {{ title }}
        </p>
      </div>
    </div>

    <div class="row">
      <div class="col-md-8">
        <Track v-for="track in tracks" :key="track.id" :track="track" />
      </div>
    </div>

    <div class="row">
      <div class="col-md-8">
        <b-pagination-nav :link-gen="linkGen" :number-of-pages="perPage"
                          use-router @change="onPageChanged"
        />
      </div>
    </div>
  </div>
</template>

<script>
import Track from '../track/track.vue'

const Timeline = {
  components: {
    Track
  },
  props: [
    'timelineName',
    'title',
    'userId'
  ],
  data: () => ({
    tracks: [],
    perPage: 1,
    currentPage: 1,
    timelineError: ''
  }),
  created () {
    this.currentPage = this.$route.query.page || 1
    console.log('loading timeline: ' + this.title)
    this.fetchTimeline()
  },
  methods: {
    onPageChanged (page) {
      this.currentPage = page
      this.fetchTimeline()
    },
    linkGen (pageNum) {
      return pageNum === 1 ? '?' : `?page=${pageNum}`
    },
    async fetchTimeline () {
      console.log(`fetching timeline ${this.timelineName} page ${this.currentPage}`)
      await this.$store.state.api.backendInteractor.fetchTimeline({ timeline: this.timelineName, page: this.currentPage, userId: this.userId })
        .then((tracks) => {
          this.tracks = tracks.items
          this.perPage = tracks.totalPages
          console.log(tracks.page)
          this.currentPage = tracks.page
          console.log('timeline fetched')
        })
        .catch((e) => {
          console.log('cannot fetch timeline: ' + e.message)
          this.timelineError = e
        })
    }
  }
}

export default Timeline
</script>
