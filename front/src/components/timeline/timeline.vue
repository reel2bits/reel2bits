<template>
  <div v-if="timelineError" class="row justify-content-md-center timeline">
    <div class="col-md-8">
      <b-alert v-if="timelineError" variant="danger" show>
        {{ timelineError }}
      </b-alert>
    </div>
  </div>
  <div v-else class="timeline">
    <div class="row">
      <div v-if="tracks.length > 0" class="col-md-12">
        <div v-for="status in tracks" :key="status.id" :status="status"
             class="status"
        >
          <Track v-if="status.type==='track'" :key="status.id" :track="status" />
          <Album v-if="status.type==='album'" :key="status.id" :album="status" />
        </div>
      </div>
      <div v-else class="col-md-12">
        <div v-if="timelineLoaded">
          <translate translate-context="Content/Timeline/*/Empty">
            Nothing to show
          </translate>
        </div>
      </div>
    </div>

    <div v-if="tracks.length > 0" class="row">
      <div class="col-md-8">
        <b-pagination-nav :link-gen="linkGen" :number-of-pages="perPage"
                          use-router @change="onPageChanged"
        />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "../../_variables.scss";

div.timeline {
  margin-top: 0.5em;
}

div.status {
  margin-bottom: 0.5em;
  padding-bottom: 0.5em;
  border-bottom: 0.1em dotted $blue;
}
</style>

<script>
import Track from '../track/track.vue'
import Album from '../album/album.vue'

const Timeline = {
  components: {
    Track,
    Album
  },
  props: [
    'timelineName',
    'userId'
  ],
  data: () => ({
    tracks: [],
    perPage: 1,
    currentPage: 1,
    timelineError: '',
    timelineLoaded: false
  }),
  created () {
    this.currentPage = this.$route.query.page || 1
    console.log('loading timeline: ' + this.timelineName)
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
          this.timelineLoaded = true
        })
        .catch((e) => {
          console.log('cannot fetch timeline: ' + e.message)
          this.timelineError = e
          this.timelineLoaded = false
          this.$bvToast.toast(this.$pgettext('Content/Timeline/Toast/Error/Message', 'Cannot load timeline'), {
            title: this.$pgettext('Content/Timeline/Toast/Error/Title', 'Timeline'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'danger'
          })
        })
    }
  }
}

export default Timeline
</script>
