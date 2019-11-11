<template>
  <div>
    <div v-if="someoneUploadedOn" class="flex-fill my-2">
      <b-link :to="{ name: 'user-profile', params: { name: track.account.screen_name } }" class="text-decoration-none">
        <img :src="track.account.profile_image_url" :alt="userAvatarAlt"
             class="rounded-circle mr-1"
             width="24"
             height="24"
        >
      </b-link>
      <span class="align-middle">
        <b-link :to="userProfileLink" class="text-decoration-none">
          {{ track.account.name }}
        </b-link>
        <translate translate-context="Content/Track/Single track in timelines, part of 'XXX >>uploaded a track<< YYY times ago'" :translate-params="{publishedAgo: publishedAgo}" :title="track.uploaded_on">
          uploaded a track %{publishedAgo}
        </translate>
      </span>
    </div>
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
          <div v-if="!someoneUploadedOn" class="col-3 px-0 mx-0 text-right" :title="track.uploaded_on">
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
            <b-button v-if="track.media_orig && processingDone" :href="track.media_orig" variant="link"
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
          <div v-if="processingDone" class="ml-auto row align-items-center mr-0">
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
import WaveSurfer from 'wavesurfer.js'
import moment from 'moment'
import { mapState } from 'vuex'
import generateProfileLink from 'src/services/user_profile_link_generator/user_profile_link_generator.js'

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
    },
    someoneUploadedOn: {
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
      },
      isPlaying: false
    }
  },
  computed: {
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
    },
    userAvatarAlt () {
      let msg = this.$pgettext('Content/Track/Image/User Avatar alt', '%{username} avatar')
      return this.$gettextInterpolate(msg, { username: this.track.account.screen_name })
    },
    userProfileLink () {
      return this.generateUserProfileLink(this.track.account.id, this.track.account.screen_name)
    }
  },
  watch: {
    'track': 'reloadTrack', // if track change, reload wavesurfer
    '$store.state.player.track': 'stopPlaying'
  },
  created () {
    console.log('initiating wavesurfer')
    if (!this.processingDone) {
      return // no wavesurfer initialisation if processing isn't done
    }
    this.$nextTick(() => {
      let opts = {
        container: `#${this.wavesurferContainer}`,
        height: 40,
        progressColor: '#C728B6',
        waveColor: '#C8D1F4',
        cursorColor: '#313DF2',
        backend: 'MediaElementWebAudio' // Not another one, benefits of MediaElement speed with WebAudio functionalities
      }
      // TODO: WebAudio (default) seems a bit slow to start the playback with ~1/2s delay
      if (!this.track.waveform) {
        opts['normalize'] = true
      }
      this.wavesurfer = WaveSurfer.create(opts)

      this.wavesurfer.on('ready', () => {
        // This will never trigger with pre-processed waveform
        // https://github.com/katspaugh/wavesurfer.js/issues/1244
        this.playerTimeTot = moment.utc(this.wavesurfer.getDuration() * 1000).format('HH:mm:ss')
      })

      this.wavesurfer.on('audioprocess', () => {
        console.log('wavesurfer audioprocessing')
        this.playerTimeCur = moment.utc(this.wavesurfer.getCurrentTime() * 1000).format('HH:mm:ss')
      })

      this.wavesurfer.on('seek', () => {
        console.log('wavesurfer seeking')
        this.playerTimeCur = moment.utc(this.wavesurfer.getCurrentTime() * 1000).format('HH:mm:ss')
      })

      this.wavesurfer.on('play', () => {
        this.isPlaying = true
        this.$emit('updateLogoSpinDuration', true)
      })

      this.wavesurfer.on('pause', () => {
        this.isPlaying = false
        this.$emit('updateLogoSpinDuration', false)
      })

      this.wavesurfer.on('finish', () => {
        this.$store.commit('playerStoppedPlaying')
      })

      this.loadWavesurfer()
    })
  },
  destroyed () {
    if (this.wavesurfer && this.wavesurfer.isPlaying()) {
      this.wavesurfer.stop()
    }
    this.$emit('updateLogoSpinDuration', false)
  },
  methods: {
    generateUserProfileLink (id, name) {
      return generateProfileLink(id, name, this.$store.state.instance.restrictedNicknames)
    },
    togglePlay: function () {
      if (this.wavesurfer.isPlaying()) {
        this.$store.commit('playerStoppedPlaying')
      } else {
        this.$store.commit('playerStartedPlaying', this.track)
      }
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    },
    loadWavesurfer (autoplay = false) {
      console.log(`loading track ${this.track.id}`)
      // Stop wavesurfer and empty waveform
      this.wavesurfer.stop()
      this.wavesurfer.empty()

      // Load new file and waveform
      // Create an <audio> Element
      let audio = document.createElement('audio')
      // Don't forget to set the id to an unique one
      audio.setAttribute('id', `audio-${this.wavesurferContainer}`)
      // Set the source
      audio.src = this.track.media_transcoded
      // Set crossOrigin to anonymous to avoid CORS restrictions
      audio.crossOrigin = 'anonymous'

      if (this.track.waveform) {
        console.log('waveform available: true')
        this.wavesurfer.load(audio, this.track.waveform.data)
      } else {
        console.log('waveform available: false')
        this.wavesurfer.load(audio)
      }

      // Workaround because of wavesurfer issue which can't fire event or do anything unless
      // you hit play, when using pre-processed waveform...
      this.playerTimeTot = moment.utc(this.track.metadatas.duration * 1000).format('HH:mm:ss')

      // If autoplay, play
      if (autoplay) {
        this.wavesurfer.play()
        this.$store.commit('playerStartedPlaying', this.track)
      }
    },
    reloadTrack () {
      this.loadWavesurfer(true)
    },
    stopPlaying () {
      console.log('asked playing !!!')
      // If the current state playing track is not the same as local one, stop playback
      if (this.$store.state.player.track !== this.track) {
        if (this.wavesurfer.isPlaying()) {
          this.wavesurfer.stop()
        }
      }
    }
  }
}
</script>
