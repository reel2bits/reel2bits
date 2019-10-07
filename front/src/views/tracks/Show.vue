<template>
  <div v-if="trackError || !track" class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="trackError" variant="danger" show>
        {{ trackError }}
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
      <div class="d-flex my-4">
        <img :src="track.picture_url" class="d-flex mr-3"
             style="width:112px; height:112px;"
        >
        <div class="flex-fill">
          <div class="d-flex">
            <h1 class="flex-fill h5" :title="track.title">
              {{ track.title | truncate(45) }}
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
            <translate translate-context="Content/TrackShow/Alert/Not available">
              Track not yet available.
            </translate>
          </div>

          <div class="pt-0 d-flex">
            <div class="btn-group" role="group" :aria-label="labels.ariaTrackActions">
              <b-button :href="track.media_orig" variant="link"
                        class="text-decoration-none pl-0"
              >
                <i class="fa fa-cloud-download" aria-hidden="true" /> <translate translate-context="Content/TrackShow/Button">
                  Download
                </translate>
              </b-button>
              <div v-if="isOwner">
                <b-button variant="link" class="text-decoration-none"
                          @click.prevent="editTrack"
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
                <b-modal id="modal-delete" :title="labels.deleteModalTitle" @ok="deleteTrack">
                  <p v-translate="{title: track.title}" class="my-4" translate-context="Content/TrackShow/Modal/Delete/Content">
                    Are you sure you want to delete '%{ title }' ?
                  </p>
                </b-modal>
              </div>
            </div>
            <div class="ml-auto align-self-end">
              <span v-if="isPlaying" class="text-secondary px-2">{{ playerTimeCur }}</span> <span class="text-muted">{{ playerTimeTot }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- genre and tags -->
      <div class="d-flex p-2">
        <div class="p-2">
          <i class="fa fa-folder-o" aria-hidden="true" />
          <translate v-if="!track.genre" translate-context="Content/TrackShow/Track genre">
            No genre defined
          </translate>
          <template v-else>
            {{ track.genre }}
          </template>
        </div>

        <div class="p-2">
          <i class="fa fa-tags" aria-hidden="true" /> <translate translate-context="Content/TrackShow/Track tags">
            No tags
          </translate>
        </div>
      </div>

      <div>
        <p class="h6">
          {{ track.title }}
        </p>
        <blockquote class="blockquote">
          <p class="small">
            {{ track.description }}
          </p>
        </blockquote>
        <p v-if="track.metadatas.licence.link">
          <translate translate-context="Content/TrackShow/Track infos">
            Licence:
          </translate><a :href="track.metadatas.licence.link">{{ track.metadatas.licence.name }}</a>
        </p>
        <p v-else>
          <translate translate-context="Content/TrackShow/Track infos">
            Licence:
          </translate>{{ track.metadatas.licence.name }}
        </p>
        <p v-if="processingDone">
          <translate translate-context="Content/TrackShow/Track infos">
            Download links:
          </translate><a :href="track.media_orig"><translate translate-context="Content/TrackShow/Track infos dls">original</translate></a><span v-if="track.processing.transcode_needed">, <a :href="track.media_transcoded"><translate translate-context="Content/TrackShow/Track infos dls">transcoded mp3</translate></a></span>.
        </p>
      </div>

      <!-- Tabs -->
      <div v-if="processingDone">
        <ul class="nav mt-5 pb-2">
          <!-- disabled for now
          <li class="nav-item pr-3">
            <a class="nav-link" href="#">
              <translate translate-context="Content/TrackShow/Track federation tab title" :translate-params="{count: track.comments}">
                %{ count } Comments
              </translate>
            </a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">
              <translate translate-context="Content/TrackShow/Track federation tab title" :translate-params="{count: track.favorited}">
                %{ count } Likes
              </translate>
            </a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">
              <translate translate-context="Content/TrackShow/Track federation tab title" :translate-params="{count: track.reblogged}">
                %{ count } Reposts
              </translate>
            </a>
          </li>
          -->
          <li class="nav-item px-3 border-left">
            <a v-translate translate-context="Content/TrackShow/Track metadatas tab title" class="nav-link active"
               href="#"
            >Metadatas</a>
          </li>
        </ul>
        <div class="border-top border-bottom py-4 my-4">
          <div class="row">
            <div class="col-sm-6">
              <h4 v-translate translate-context="Content/TrackShow/Track metadatas headline">
                Metadatas of the original file
              </h4>
              <table class="table table-sm my-0">
                <tbody>
                  <tr>
                    <th scope="row" class="col-md-2 border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        Type
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.type }}
                    </td>
                  </tr>
                  <tr v-if="track.metadatas.codec">
                    <th scope="row" class="border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        Codec
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.codec }}
                    </td>
                  </tr>
                  <tr>
                    <th scope="row" class="border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        Channels
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.channels }}
                    </td>
                  </tr>
                  <tr>
                    <th scope="row" class="border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        Sample rate
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.rate }}
                    </td>
                  </tr>
                  <tr v-if="track.metadatas.bitrate && track.metadatas.bitrate_mode">
                    <th scope="row" class="border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        Bit rate
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.bitrate }} {{ track.metadatas.bitrate_mode }}
                    </td>
                  </tr>
                  <tr>
                    <th scope="row" class="col-md-2 border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata/Size">
                        File size
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.file_size | humanizeSize }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="track.processing.transcode_needed" class="col-sm-6">
              <h4 v-translate translate-context="Content/TrackShow/Track metadatas headline">
                Metadatas of the transcoded file
              </h4>
              <table class="table table-sm my-0">
                <tbody>
                  <tr>
                    <th scope="row" class="col-md-2 border-0 font-weight-normal">
                      <translate translate-context="Content/TrackShow/Track metadata">
                        File size
                      </translate>
                    </th>
                    <td class="border-0 font-weight-bold">
                      {{ track.metadatas.transcode_file_size | humanizeSize }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <div v-else>
        <hr>
        <b-alert v-translate show variant="info"
                 translate-context="Content/TrackShow/Track not processed alert"
        >
          This song is not yet processed.
        </b-alert>

        <template v-if="track.processing.transcode_state === 3">
          <p>
            <translate translate-context="Content/TrackShow/ErrorOccured text">
              An error occured while processing the track, you can click the following link to retry (if it's only a one-time temporary error).
            </translate>
          </p>
          <b-button :disabled="processingResetted" type="submit"
                    variant="primary" @click.prevent="retryProcessing"
          >
            {{ retryButtonLabel }}
          </b-button>
          <br><br>
        </template>

        <template v-if="trackLogs.length > 0">
          <h5>Current processing log:</h5>
          <b-table show-empty :items="trackLogs" :fields="trackLogsFields" />
        </template>
      </div>
    </div>

    <div v-if="track" class="col-md-4 d-flex flex-column">
      <Sidebar />
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
import WaveSurfer from 'wavesurfer.js'
import moment from 'moment'
import playerUtils from '../../services/player_utils/player_utils.js'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'
import Sidebar from '../../components/sidebar/sidebar.vue'

export default {
  components: {
    Sidebar
  },
  filters: {
    humanizeSize: function (num) {
      if (num === 0) {
        return 0
      }
      let ffs = fileSizeFormatService.fileSizeFormat(num)
      return ffs.num + ' ' + ffs.unit
    }
  },
  data () {
    return {
      track: null,
      trackError: '',
      deleteError: null,
      processing_done: false,
      isOwner: false,
      wavesurfer: null,
      playerTimeCur: '00:00',
      playerTimeTot: '00:00',
      userId: null,
      processingResetted: false,
      trackLogs: [],
      trackLogsFields: [
        {
          key: 'date',
          label: this.$pgettext('Content/Track(Logs)/Table/Heading', 'Date')
        },
        {
          key: 'level',
          label: this.$pgettext('Content/Track(Logs)/Table/Heading', 'Level')
        },
        {
          key: 'message',
          label: this.$pgettext('Content/Track(Logs)/Table/Heading', 'Message')
        }
      ]
    }
  },
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
    },
    labels () {
      return {
        ariaTrackActions: this.$pgettext('Content/TrackShow/Aria/Track actions', 'Track actions'),
        deleteModalTitle: this.$pgettext('Content/TrackShow/Modal/Delete/Title', 'Deleting track')
      }
    },
    retryButtonLabel () {
      if (this.processingResetted) {
        return this.$pgettext('Content/TrackShow/Button/Text', 'retry scheduled')
      } else {
        return this.$pgettext('Content/TrackShow/Button/Text', 'retry')
      }
    }
  },
  created () {
    const user = this.$store.getters.findUser(this.userName)
    if (user) {
      this.userId = user.id
    } // else, oops
    this.fetchTrack()
      .then((v) => {
        if (!this.trackError && this.track && this.processingDone) {
          console.log('initiating wavesurfer')
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
        } else {
          if (!this.trackError && this.track) {
            this.fetchTrackLogs()
          }
        }
      })
  },
  destroyed () {
    this.wavesurfer.stop()
    this.$emit('updateLogoSpinDuration', false)
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      // || quick fix before we fully implement id or username thing
      await this.$store.state.api.backendInteractor.trackFetch({ userId: this.userId || this.userName, trackId: this.trackId })
        .then((status) => {
          this.track = status
          this.processing_done = this.track.processing.done
          this.isOwner = (this.track.account.screen_name === this.$store.state.users.currentUser.screen_name)
          console.log('track fetched')
        })
        .catch((e) => {
          console.log('cannot fetch track:' + e.message)
          this.trackError = e
        })
    },
    async fetchTrackLogs () {
      console.log('fetching track logs...')
      await this.$store.state.api.backendInteractor.fetchTrackLogs({ userId: this.userId, trackId: this.trackId })
        .then((data) => {
          this.trackLogs = data.logs
        })
        .catch((e) => {
          console.log('cannot fetch track logs:' + e.message)
          this.trackError = e
        })
    },
    async editTrack () {
      if (!this.isOwner) { return }
      console.log('want to edit track')
      this.$router.push({ name: 'tracks-edit', params: { userId: this.track.account.id, trackId: this.track.slug } })
    },
    async deleteTrack () {
      if (!this.isOwner) { return }
      console.log('deleting track')
      try {
        await this.$store.state.api.backendInteractor.trackDelete({ userId: this.track.account.id, trackId: this.trackId })
      } catch (e) {
        console.log('an error occured')
        console.log(e)
        this.deleteError = this.$pgettext('Content/TrackShow/Error', 'an error occured while deleting the track.')
        return
      }
      this.$router.push({ name: 'user-profile', params: { name: this.$store.state.users.currentUser.screen_name } })
    },
    togglePlay: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    },
    async retryProcessing () {
      console.log('retrying processing...')
      await this.$store.state.api.backendInteractor.trackRetryProcessing({ userId: this.userId, trackId: this.trackId })
        .then(() => {
          console.log('ok')
          this.processingResetted = true
          this.$bvToast.toast(this.$pgettext('Content/TrackShow/Toast/Info/Message', 'Processing resetted.'), {
            title: this.$pgettext('Content/TrackShow/Toast/Info/Title', 'Track processing'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'info'
          })
        })
        .catch((e) => {
          console.log('cannot reset', e)
          this.$bvToast.toast(this.$pgettext('Content/TrackShow/Toast/Info/Message', 'Cannot reset processing.'), {
            title: this.$pgettext('Content/TrackShow/Toast/Info/Title', 'Track processing'),
            autoHideDelay: 10000,
            appendToast: false,
            variant: 'danger'
          })
        })
    }
  }
}
</script>
