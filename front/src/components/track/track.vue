<template>
  <div>
    <div class="flex-fill my-2">
      <b-link :to="{ name: 'user-profile', params: { name: track.account.screen_name } }" class="text-decoration-none">
        <img :src="track.account.profile_image_url" :alt="userAvatarAlt"
             class="rounded-circle mr-1"
             width="24"
             height="24"
        >
      </b-link>
      <span class="align-middle">
        <b-link :to="{ name: 'user-profile', params: { name: track.account.screen_name } }" class="text-decoration-none">
          {{ track.account.name }}
        </b-link>
        <translate translate-context="Content/Track/Single track in timelines, part of 'XXX >>uploaded a track<< YYY times ago'" :translate-params="{publishedAgo: publishedAgo}" :title="track.uploaded_on">
          uploaded a track %{publishedAgo}
        </translate>
      </span>
    </div>
    <div class="d-flex my-12">
      <b-link :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }">
        <img :src="track.picture_url" class="d-flex mr-3"
             style="width:112px; height:112px;"
        >
      </b-link>
      <div class="flex-fill">
        <div class="d-flex">
          <h2 class="flex-fill h5" :title="track.title">
            <b-link :to="{ name: 'tracks-show', params: { username: track.account.screen_name, trackId: track.slug } }"
                    class="text-body text-decoration-none"
            >
              {{ track.title | truncate(60) }}
            </b-link>
          </h2>
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
          <div class="btn-group" role="group">
            <b-button :href="track.media_orig" variant="link"
                      class="text-decoration-none pl-0"
            >
              <i class="fa fa-cloud-download" aria-hidden="true" /> <translate translate-context="Content/Track/Button">
                Download
              </translate>
            </b-button>
          </div>
          <div class="ml-auto row align-items-center mr-0">
            <span v-if="isPlaying" class="text-secondary px-2">{{ playerTimeCur }}</span> <span class="text-muted">{{ playerTimeTot }}</span>
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
    },
    userAvatarAlt () {
      let msg = this.$pgettext('Content/Track/Image/User Avatar alt', '%{username} avatar')
      return this.$gettextInterpolate(msg, { username: this.track.account.screen_name })
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
