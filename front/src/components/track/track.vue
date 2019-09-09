<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <div class="d-flex my-12">
          <b-link :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }">
            <img :src="track.picture_url" class="d-flex mr-3"
                 style="width:112px; height:112px;"
            >
          </b-link>
          <div class="flex-fill">
            <div class="d-flex">
              <h1 class="flex-fill h5" :title="track.title">
                <b-link :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }">
                  {{ track.title | truncate(45) }}
                </b-link>
              </h1>
              <div class="d-flex" :title="track.uploaded_on">
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

            <div class="pt-0 d-flex">
              <div>
                <translate translate-context="Content/Track/Single track in timelines, 'By: xxx'">
                  By:
                </translate>
                <b-link :to="{ name: 'user-profile', params: { name: track.account.screen_name } }" class="text-decoration-none text-body">
                  {{ track.account.name }}
                </b-link>
              </div>
              <div class="ml-auto align-self-end">
                <span class="text-secondary">{{ playerTimeCur }}</span> <span class="text-muted">{{ playerTimeTot }}</span>
              </div>
            </div>
          </div>
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
import moment from 'moment'
import WaveSurfer from 'wavesurfer.js'
import playerUtils from '../../services/player_utils/player_utils.js'

const Track = {
  props: [
    'track'
  ],
  data: () => ({
    wavesurfer: null,
    playerTimeCur: '00:00',
    playerTimeTot: '00:00'
  }),
  computed: {
    processingDone () {
      return (this.track.processing.done && this.track)
    },
    publishedAgo () {
      return moment(this.track.uploaded_on).fromNow()
    },
    wavesurferContainer () {
      return `waveform-${this.track.id}`
    },
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
    }
  },
  created () {
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

      if (this.track.waveform) {
        console.log('smoothing the waveform')
        let max = Math.max.apply(Math, this.track.waveform.data)
        this.wavesurfer.load(this.track.media_transcoded, this.track.waveform.data.map(p => p / max))
      } else {
        this.wavesurfer.load(this.track.media_transcoded)
      }

      // Workaround because of wavesurfer issue which can't fire event or do anything unless
      // you hit play, when using pre-processed waveform...
      this.playerTimeTot = moment.utc(this.track.metadatas.duration * 1000).format('mm:ss')
    })
  },
  methods: {
    togglePlay: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    }
  }
}

export default Track
</script>
