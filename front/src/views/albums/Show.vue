<template>
  <div v-if="albumError || !album" class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="albumError" variant="danger" show>
        {{ albumError }}
      </b-alert>
    </div>
  </div>
  <div v-else class="row">
    <div class="col-md-8">
      <b-alert v-if="deleteError" variant="danger" show
               dismissible
               @dismissed="deleteError=null"
      >
        {{ deleteError }}
      </b-alert>

      <h4>{{ album.title }}</h4>
      <div class="btn-group" role="group" aria-label="Albums actions">
        <div v-if="isOwner">
          <b-button variant="link" class="text-decoration-none"
                    @click.prevent="editAlbum"
          >
            <i class="fa fa-pencil" aria-hidden="true" /> Edit
          </b-button>
          <b-button v-b-modal.modal-delete variant="link"
                    class="text-decoration-none"
          >
            <i class="fa fa-times" aria-hidden="true" /> Delete
          </b-button>
          <b-modal id="modal-delete" title="Deleting album" @ok="deleteAlbum">
            <p class="my-4">
              Are you sure you want to delete '{{ album.title }}' ?
            </p>
          </b-modal>
        </div>
      </div>

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
          <div id="waveform" class="flex-fill" />
        </div>

        <div>
          <draggable tag="ul" :list="tracksList" class="list-group"
                     handle=".handle"
          >
            <li v-for="element in tracksList" :key="element.title" class="list-group-item">
              <i class="fa fa-align-justify handle" />
              <i v-if="currentTrack.id == element.id" class="fa fa-play" />
              <span class="text" @click.prevent="loadWavesurferById(element.id, true)">{{ element.title }}</span>
              <span class="text-right">{{ element.length }}</span>
            </li>
          </draggable>
        </div>
      </div>
    </div>

    <div v-if="album" class="col-md-4 d-flex flex-column">
      <!-- Profile Card -->
      <UserCard :user="album.account" />
      <!-- Footer -->
      <Footer />
    </div>
  </div>
</template>

<style scoped lang="scss">
button.playPause {
  margin-right: 5px;
}
</style>

<script>
import { mapState } from 'vuex'
import moment from 'moment'
import UserCard from '../../components/user_card/user_card.vue'
import Footer from '../../components/footer/footer.vue'
import playerUtils from '../../services/player_utils/player_utils.js'
import WaveSurfer from 'wavesurfer.js'
import draggable from 'vuedraggable'

export default {
  components: {
    draggable,
    UserCard,
    Footer
  },
  data: () => ({
    album: null,
    albumError: null,
    deleteError: null,
    isOwner: false,
    userId: null,
    wavesurfer: null,
    tracksList: [],
    currentTrack: null,
    playerTimeCur: '00:00',
    playerTimeTot: '00:00'
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    albumId () {
      return this.$route.params.albumId
    },
    userName () {
      return this.$route.params.username
    },
    publishedAgo () {
      return moment(this.album.uploaded_on).fromNow()
    },
    isPlaying () {
      if (!this.wavesurfer) return false
      return this.wavesurfer.isPlaying()
    }
  },
  created () {
    const user = this.$store.getters.findUser(this.userName)
    if (user) {
      this.userId = user.id
    } // else, oops
    this.fetchAlbum()
      .then((album) => {
        // Build the reordering list
        this.tracksList = this.album.tracks.map(p => { return { id: p.id, title: p.title, length: p.metadatas.duration } })
        // Get the first track
        // Reorder
        this.album.tracks.sort((a, b) => { return a.album_order - b.album_order })
        // Get the first
        this.currentTrack = this.album.tracks[0]
        // Create the wavesurfer player and init
        this.$nextTick(() => {
          let opts = {
            container: '#waveform',
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
      })
  },
  methods: {
    async fetchAlbum () {
      // || quick fix before we fully implement id or username thing
      await this.$store.state.api.backendInteractor.albumFetch({ userId: this.userId || this.userName, albumId: this.albumId })
        .then((data) => {
          this.album = data
          this.isOwner = (this.album.account.screen_name === this.$store.state.users.currentUser.screen_name)
        })
    },
    async editAlbum () {
      if (!this.isOwner) { return }
      console.log('want to edit album')
      this.$router.push({ name: 'albums-edit', params: { userId: this.album.account.id, albumId: this.album.slug } })
    },
    async deleteAlbum () {
      if (!this.isOwner) { return }
      console.log('deleting album')
      try {
        await this.$store.state.api.backendInteractor.albumDelete({ userId: this.album.account.id, albumId: this.albumId })
      } catch (e) {
        console.log('an error occured')
        console.log(e)
        this.deleteError = 'an error occured while deleting the album.'
        return
      }
      this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
    },
    togglePlay: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
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
        this.loadWavesurfer(track, autoplay)
      } // else oops
    }
  }
}
</script>
