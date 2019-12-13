<template>
  <div class="row">
    <div class="col-md-12">
      <b-link :to="{ name: 'albums-show', params: { username: album.account.screen_name, albumId: album.slug } }">
        <h4>{{ album.title }}</h4>
      </b-link>

      <ContentAudioPlayer v-if="currentTrack" :track="currentTrack" />

      <div>
        <draggable ref="draggable" tag="ul"
                   :list="tracksList"
                   class="list-group album-tracks-list"
                   handle=".handle" disabled="true"
        >
          <li v-for="element in tracksList" :key="element.id" class="list-group-item tracks-list">
            <span class="actions">
              <i v-if="currentTrack.id == element.id" class="fa fa-play" />
            </span>
            <span class="text" @click.prevent="changeCurrentTrack(element.id)">
              {{ element.title }}
            </span>
            <span class="pull-right">
              {{ element.length.toFixed(2) }}
            </span>
          </li>
        </draggable>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
button.playPause {
  margin-right: 5px;
}
li.tracks-list span.actions {
  width: 3em;
  float: left;
}
li.tracks-list span.actions i.fa-play {
  padding-left: 5px;
}

ul.album-tracks-list {
  max-height: 12em;
  overflow-y: scroll;
}
</style>

<script>
import moment from 'moment'
import draggable from 'vuedraggable'
import ContentAudioPlayer from '../../components/content_audio_player/content_audio_player.vue'

const Album = {
  props: [
    'album'
  ],
  components: {
    draggable,
    ContentAudioPlayer
  },
  data: () => ({
    tracksList: [],
    currentTrack: null
  }),
  computed: {
    publishedAgo () {
      return moment(this.album.uploaded_on).fromNow()
    },
    isPlaying () {
      if (!this.wavesurfer) return false
      return this.wavesurfer.isPlaying()
    }
  },
  created () {
    // Get the first track and set initial tracks list
    // Reorder by album_order
    this.album.tracks.sort((a, b) => { return a.album_order - b.album_order })
    // Build the reordering list
    this.tracksList = this.album.tracks.map(p => { return { id: p.id, title: p.title, length: p.metadatas.duration } })
    // Get the first
    this.currentTrack = this.album.tracks[0]
  },
  methods: {
    changeCurrentTrack (trackId) {
      console.log(`changing track by id ${trackId}`)
      // Find track
      const track = this.album.tracks.find(t => t.id === trackId)
      if (track) {
        console.log(track)
        this.currentTrack = track
      } else {
        this.$bvToast.toast(null, {
          title: this.$pgettext('Content/Album/Toast/Error/Title', 'Cannot find track.'),
          autoHideDelay: 5000,
          appendToast: false,
          variant: 'danger'
        })
      }
    }
  }
}

export default Album
</script>
