<template>
  <div class="d-flex mb-3">
    <b-link v-if="clickableTitle" :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }">
      <img :src="track.picture_url" class="d-flex mr-3"
           style="width:112px; height:112px;"
      >
    </b-link>
    <template v-else>
      <img :src="track.picture_url" class="d-flex mr-3"
           style="width:112px; height:112px;"
      >
    </template>
    <div class="flex-fill">
      <div class="row px-0 mx-0">
        <h1 class="col px-0 mx-0 h5 text-truncate" :title="track.title">
          <b-link v-if="clickableTitle" :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }" class="text-body text-decoration-none">
            {{ track.title }}
          </b-link>
          <template v-else>
            {{ track.title }}
          </template>
        </h1>
        <div class="col-3 px-0 mx-0 text-right" :title="track.uploaded_on">
          {{ publishedAgo }}
        </div>
      </div>
      <div v-if="processingDone" class="d-flex my-2">
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
      <div v-else-if="processingDone" class="alert alert-dark">
        <translate translate-context="Content/TrackShow/Alert/Not available">
          Track not yet available.
        </translate>
      </div>

      <div class="pt-0 d-flex">
        <div class="btn-group" role="group" :aria-label="labels.ariaTrackActions">
          <b-button v-if="track.media_orig" :href="track.media_orig" variant="link"
                    class="text-decoration-none pl-0"
          >
            <i class="fa fa-cloud-download" aria-hidden="true" /> <translate translate-context="Content/TrackShow/Button">
              Download
            </translate>
          </b-button>
          <div v-if="isOwner && editLink">
            <b-button variant="link" class="text-decoration-none"
                      @click.prevent="editLink"
            >
              <i class="fa fa-pencil" aria-hidden="true" /> <translate translate-context="Content/TrackShow/Button">
                Edit
              </translate>
            </b-button>
            <b-button v-b-modal.modal-delete variant="link"
                      class="text-decoration-none"
            >
              <i class="fa fa-times" aria-hidden="true" /> <translate translate-context="Content/TrackShow/Button">
                Delete
              </translate>
            </b-button>
            <b-modal id="modal-delete" :title="labels.deleteModalTitle" @ok="deleteLink">
              <p v-translate="{title: track.title}" class="my-4" translate-context="Content/TrackShow/Modal/Delete/Content">
                Are you sure you want to delete '%{ title }' ?
              </p>
            </b-modal>
          </div>
        </div>
        <div class="ml-auto row align-items-center mr-0">
          <span v-if="isPlaying" class="text-secondary px-2">{{ playerTimeCur }}</span> <span class="text-muted">{{ playerTimeTot }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
button.playPause {
  margin-right: 5px;
}
</style>

<script>
import playerUtils from '../../services/player_utils/player_utils.js'
import WaveSurfer from 'wavesurfer.js'
import moment from 'moment'
import { mapState } from 'vuex'

export default {
  props: {
    track: {
      type: Object,
      required: true
    },
    editLink: {
      type: Function,
      required: false
    },
    deleteLink: {
      type: Function,
      required: false
    },
    clickableTitle: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data () {
    return {
      wavesurfer: null,
      playerTimeCur: '00:00',
      playerTimeTot: '00:00',
      labels () {
        return {
          ariaTrackActions: this.$pgettext('Content/TrackShow/Aria/actions', 'actions'),
          deleteModalTitle: this.$pgettext('Content/TrackShow/Modal/Delete/Title', 'Deleting item')
        }
      }
    }
  },
  computed: {
    isPlaying () {
      if (!this.wavesurfer) return false
      return this.wavesurfer.isPlaying()
    },
    svgDuration () {
      if (!this.wavesurfer) return '0'
      if (this.wavesurfer.isPlaying()) {
        return '10s'
      } else {
        return '0'
      }
    },
    publishedAgo () {
      return moment(this.track.uploaded_on).fromNow()
    },
    processingDone () {
      return (this.track.processing.done && this.track)
    },
    ...mapState({
      currentUser: state => state.users.currentUser
    }),
    isOwner () {
      return this.track.account.screen_name === this.currentUser.screen_name
    },
    wavesurferContainer () {
      return `waveform-${this.track.slug}`
    }
  },
  watch: {
    'track': 'reloadTrack' // if track change, reload wavesurfer
  },
  created () {
    console.log('initiating wavesurfer')
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
      if (!this.track.waveform) {
        opts['normalize'] = true
      }
      this.wavesurfer = WaveSurfer.create(opts)

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

      this.loadWavesurfer()
    })
  },
  destroyed () {
    this.wavesurfer.stop()
    this.$emit('updateLogoSpinDuration', false)
  },
  methods: {
    togglePlay: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    },
    loadWavesurfer (autoplay = false) {
      console.log(`loading track ${this.track.id}`)
      // Stop wavesurfer and empty waveform
      this.wavesurfer.stop()
      this.wavesurfer.empty()

      // Load new file and waveform
      if (this.track.waveform) {
        console.log('waveform available: true')
        let max = Math.max.apply(Math, this.track.waveform.data)
        this.wavesurfer.load(this.track.media_transcoded, this.track.waveform.data.map(p => p / max))
      } else {
        console.log('waveform available: false')
        this.wavesurfer.load(this.track.media_transcoded)
      }

      // Workaround because of wavesurfer issue which can't fire event or do anything unless
      // you hit play, when using pre-processed waveform...
      this.playerTimeTot = moment.utc(this.track.metadatas.duration * 1000).format('mm:ss')

      // If autoplay, play
      if (autoplay) {
        this.wavesurfer.play()
      }
    },
    reloadTrack () {
      this.loadWavesurfer(true)
    }
  }
}
</script>
