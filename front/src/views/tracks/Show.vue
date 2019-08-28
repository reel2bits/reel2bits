<template>
  <div v-if="trackError && !track" class="row justify-content-md-center">
    <div class="col-md-6" />
  </div>
  <div v-else class="row">
    <div class="col-md-8">
      <div class="d-flex my-4">
        <img :src="track.picture_url" class="d-flex mr-3"
             style="width:112px; height:112px; background: #C8D1F4; "
        >
        <div class="flex-fill">
          <div class="d-flex">
            <h1 class="flex-fill h3">
              {{ track.title }}
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
            <div id="waveform" class="flex-fill" />
          </div>
          <div v-else-if="processingDone" class="alert alert-dark">
            Track not yet available.
          </div>

          <div class="pt-1 d-flex">
            <div class="btn-group" role="group" aria-label="Track actions">
              <div v-if="isOwner">
                <button type="button" class="btn btn-link py-0 pl-0" @click.prevent="editTrack">
                  <i class="fa fa-pencil" aria-hidden="true" /> Edit
                </button>
                <button type="button" class="btn btn-link py-0" @click.prevent="deleteTrack">
                  <i class="fa fa-times" aria-hidden="true" /> Delete
                </button>
              </div>
            </div>
            <div class="ml-auto align-self-end">
              <span class="text-secondary">{{ playerTimeCur }}</span> / <span class="text-muted">{{ playerTimeTot }}</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <p>{{ track.description }}</p>
        <p v-if="track.metadatas.licence.link">
          Licence: <a :href="track.metadatas.licence.link">{{ track.metadatas.licence.name }}</a>
        </p>
        <p v-else>
          Licence: {{ track.metadatas.licence.name }}
        </p>
      </div>

      <!-- Tabs -->
      <div>
        <ul class="nav mt-5 pb-2">
          <li class="nav-item pr-3">
            <a class="nav-link" href="#">{{ track.comments }} Comments</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">{{ track.favorited }} Likes</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">{{ track.reblogged }} Reposts</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link active" href="#">Metadatas</a>
          </li>
        </ul>
        <div class="border-top border-bottom py-4 my-4">
          <table class="table table-sm my-0">
            <tbody>
              <tr>
                <th scope="row" class="col-md-2 border-0 font-weight-normal">
                  Type
                </th>
                <td class="border-0 font-weight-bold">
                  {{ track.metadatas.type }}
                </td>
              </tr>
              <tr>
                <th scope="row" class="border-0 font-weight-normal">
                  Codec
                </th>
                <td class="border-0 font-weight-bold">
                  {{ track.metadatas.codec }}
                </td>
              </tr>
              <tr>
                <th scope="row" class="border-0 font-weight-normal">
                  Channels
                </th>
                <td class="border-0 font-weight-bold">
                  {{ track.metadatas.channels }}
                </td>
              </tr>
              <tr>
                <th scope="row" class="border-0 font-weight-normal">
                  Sample rate
                </th>
                <td class="border-0 font-weight-bold">
                  {{ track.metadatas.rate }}
                </td>
              </tr>
              <tr>
                <th scope="row" class="border-0 font-weight-normal">
                  Bit rate
                </th>
                <td class="border-0 font-weight-bold">
                  {{ track.metadatas.bitrate }} {{ track.metadatas.bitrate_mode }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="track" class="col-md-4 d-flex flex-column">
      <!-- Profile Card -->
      <div class="card my-4">
        <div class="card-body py-3 px-3">
          <div class="d-flex mb-2">
            <div class="d-flex rounded-circle mr-2" style="width:96px; height:96px; overflow:hidden">
              <img :src="track.account.avatar" alt="user avatar" style="height:96px;">
            </div>
            <div class="align-self-center">
              <h2 class="h2 m-0">
                {{ track.account.display_name }}
              </h2>
              <p class="h3 font-weight-normal m-0">
                @{{ track.account.username }} <button type="button" class="btn btn-primary btn-sm">
                  Follow
                </button>
              </p>
              <p class="text-muted m-0">
                <!-- Follows you -->
              </p>
            </div>
          </div>
          <p class="card-text">
            {{ track.account.note }}
          </p>
          <ul class="nav nav-fill">
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ track.account.statuses_count }}</p><p class="m-0">Tracks</p></a>
            </li>
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ track.account.reel2bits.albums_count }}</p><p class="m-0">Albums</p></a>
            </li>
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ track.account.followers_count }}</p><p class="m-0">Followers</p></a>
            </li>
            <li class="nav-item">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ track.account.following_count }}</p><p class="m-0">Following</p></a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Footer -->
      <Footer />
    </div>
  </div>
</template>

<style lang="scss">
button.playPause {
  margin-right: 5px;
}
</style>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'
import WaveSurfer from 'wavesurfer.js'
import moment from 'moment'
import Footer from '../../components/footer/footer.vue'
import playerUtils from '../../services/player_utils/player_utils.js'

export default {
  components: {
    Footer
  },
  data: () => ({
    track: null,
    trackError: '',
    processing_done: false,
    isOwner: false,
    wavesurfer: null,
    playerTimeCur: '00:00',
    playerTimeTot: '00:00'
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser,
      sourceUrl: state => state.instance.sourceUrl
    }),
    trackId () {
      return this.$route.params.trackId
    },
    userName () {
      return this.$route.params.username
    },
    processingDone () {
      return (this.processing_done && this.track)
    },
    publishedAgo () {
      return moment(this.track.uploaded_on).fromNow()
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
  mounted () {
    this.fetchTrack()
      .then((v) => {
        if (!this.trackError && this.track) {
          console.log('initiating wavesurfer')
          this.$nextTick(() => {
            let opts = {
              container: '#waveform',
              height: 40,
              progressColor: '#C728B6',
              waveColor: '#C8D1F4',
              cursorColor: '#313DF2'
            }
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
              this.$emit('updateLogoSpinDuration', '5s')
            })

            this.wavesurfer.on('pause', () => {
              this.$emit('updateLogoSpinDuration', '0s')
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
        }
      })
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      await this.$store.state.api.backendInteractor.trackFetch({ user: this.userName, trackId: this.trackId })
        .then((status) => {
          this.track = status
          this.processing_done = this.track.processing.done
          this.isOwner = (this.track.account.username === this.$store.state.users.currentUser.screen_name)
          console.log('track fetched')
        })
        .catch((e) => {
          console.log('cannot fetch track:' + e.message)
          this.trackError = e
        })
    },
    async editTrack () {
      console.log('want to edit track')
    },
    async deleteTrack () {
      console.log('want to delete track')
      if (confirm('Are you sure ?')) {
        apiService.trackDelete(this.userName, this.trackId, this.$store)
          .then(this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
          )
      }
    },
    togglePlay: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    }
  }
}
</script>
