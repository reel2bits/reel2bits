<template>
  <div class="row">
    <div class="col-md-12">
      <h4>{{ album.title }}</h4>

      <div class="d-flex my-4">
        <img :src="album.picture_url" class="d-flex mr-3"
             style="width:112px; height:112px;"
        >
        <div class="flex-fill">
          <div v-if="currentTrack" class="d-flex">
            <h1 class="flex-fill h5" :title="currentTrack.title">
              <b-link :to="{ name: 'tracks-show', params: { username: album.account.screen_name, trackId: currentTrack.slug } }">
                {{ currentTrack.title | truncate(45) }}
              </b-link>
            </h1>
            <div class="d-flex" :title="currentTrack.uploaded_on">
              {{ publishedAgo }}
            </div>
          </div>

          <div v-if="currentTrack" class="d-flex my-2">
            <b-button v-if="!isPlaying" class="playPause" variant="primary"
                      @click.prevent="togglePlay"
            >
              <i class="fa fa-play" aria-hidden="true" />
            </b-button>
            <b-button v-if="isPlaying" class="playPause" @click.prevent="togglePlay">
              <i class="fa fa-pause" aria-hidden="true" />
            </b-button>
            <div :id="wavesurferContainer" class="flex-fill" />
          </div>
          <div v-else v-translate translate-context="Content/Album/TracksList/Empty">
            No tracks in this album
          </div>

          <div v-if="currentTrack" class="pt-0 d-flex">
            <div class="ml-auto align-self-end">
              <span class="text-secondary">{{ playerTimeCur }}</span> <span class="text-muted">{{ playerTimeTot }}</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <draggable ref="draggable" tag="ul"
                   :list="tracksList"
                   class="list-group album-tracks-list"
                   handle=".handle" disabled="true"
        >
          <li v-for="element in tracksList" :key="element.title" class="list-group-item tracks-list">
            <span class="actions">
              <i v-if="currentTrack.id == element.id" class="fa fa-play" />
            </span>
            <span class="text" @click.prevent="loadWavesurferById(element.id, true)">
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
import WaveSurfer from 'wavesurfer.js'
import playerUtils from '../../services/player_utils/player_utils.js'
import draggable from 'vuedraggable'

const Album = {
  props: [
    'album'
  ],
  components: {
    draggable
  },
  data: () => ({
    tracksList: [],
    currentTrack: null,
    wavesurfer: null,
    playerTimeCur: '00:00',
    playerTimeTot: '00:00'
  }),
  computed: {
    publishedAgo () {
      return moment(this.album.uploaded_on).fromNow()
    },
    wavesurferContainer () {
      return `waveform-${this.album.id}`
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

    if (this.album.tracks.length > 0) {
      this.$nextTick(() => {
        let opts = {
          container: `#${this.wavesurferContainer}`,
          height: 40,
          progressColor: '#C728B6',
          waveColor: '#C8D1F4',
          cursorColor: '#313DF2',
          backend: 'WebAudio'
        }
        // TODO: WebAudio (default) seems a bit slow to start the playback with ~1/2s delay
        if (!this.currentTrack.waveform) {
          opts['normalize'] = true
        }
        this.wavesurfer = WaveSurfer.create(opts)

        // Wavesurfer hooks
        this.wavesurfer.on('ready', () => {
        // This will never trigger with pre-processed waveform
        // https://github.com/katspaugh/wavesurfer.js/issues/1244
          this.playerTimeTot = playerUtils.secondsTimeSpanToMS(this.wavesurfer.getDuration())
        })

        this.wavesurfer.on('audioprocess', () => {
          console.log('wavesurfer audioprocessing')
          this.playerTimeCur = playerUtils.secondsTimeSpanToMS(this.wavesurfer.getCurrentTime())
        })

        this.wavesurfer.on('seek', () => {
          console.log('wavesurfer seeking')
          this.playerTimeCur = playerUtils.secondsTimeSpanToMS(this.wavesurfer.getCurrentTime())
        })

        this.wavesurfer.on('play', () => {
          this.$emit('updateLogoSpinDuration', true)
        })

        this.wavesurfer.on('pause', () => {
          this.$emit('updateLogoSpinDuration', false)
        })

        this.wavesurfer.on('finish', () => {
        // Switch to next song
          let idx = this.album.tracks.indexOf(this.currentTrack)
          if (this.album.tracks.length >= idx + 1) {
            this.loadWavesurfer(this.album.tracks[idx + 1], true)
          }
        })

        // Load the track
        this.loadWavesurfer(this.currentTrack, false)
      })
    }
  },
  methods: {
    togglePlay: function () {
      this.wavesurfer.playPause()
    },
    loadWavesurfer (track, autoplay) {
      console.log(`loading track ${track.id}`)
      // Stop wavesurfer and empty waveform
      this.wavesurfer.stop()
      this.wavesurfer.empty()

      // Set the new current track
      this.currentTrack = track

      // Load new file and waveform
      if (track.waveform) {
        let max = Math.max.apply(Math, track.waveform.data)
        this.wavesurfer.load(track.media_transcoded, track.waveform.data.map(p => p / max))
      } else {
        this.wavesurfer.load(track.media_transcoded)
      }

      // Workaround because of wavesurfer issue which can't fire event or do anything unless
      // you hit play, when using pre-processed waveform...
      this.playerTimeTot = moment.utc(this.currentTrack.metadatas.duration * 1000).format('mm:ss')

      // If autoplay, play
      if (autoplay) {
        this.wavesurfer.play()
      }
    },
    loadWavesurferById (trackId, autoplay) {
      console.log(`loading track by id ${trackId}`)
      // Find track
      let track = this.album.tracks.find(t => t.id === trackId)
      if (track) {
        console.log(track)
        this.loadWavesurfer(track, autoplay)
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
