<template>
  <div v-if="trackError || !track" class="row justify-content-md-center">
    <div class="col-md-6">
      <b-alert v-if="trackError" variant="danger" show>
        {{ trackError }}
      </b-alert>
    </div>
  </div>
  <div v-else class="row mt-4">
    <div class="col-md-8">
      <b-alert v-if="deleteError" variant="danger" show
               dismissible
               @dismissed="deleteError=null"
      >
        {{ deleteError }}
      </b-alert>
      <ContentAudioPlayer v-if="!trackError && track && processingDone" :track="track" :edit-track="editTrack"
                          :delete-track="deleteTrack"
      />

      <!-- genre and tags -->
      <div>
        <p class="mb-1">
          {{ track.description }}
        </p>
        <div>
          <template v-if="track.genre">
            <b-badge variant="secondary"
                     class="mr-1"
            >
              <i class="fa fa-tag" aria-hidden="true" /> {{ track.genre }}
            </b-badge>
          </template><template v-if="track.tags.length > 0">
            <b-badge v-for="tag in track.tags" :key="tag" variant="primary"
                     class="mr-1"
            >
              <!--<i class="fa fa-hashtag" aria-hidden="true" />-->#{{ tag }}
            </b-badge>
          </template>
        <!--<translate v-else translate-context="Content/TrackShow/Track tags">
          No tags
        </translate> -->
        </div>
      </div>

      <!--<div>
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
      </div> -->

      <!-- Tabs -->
      <div v-if="processingDone">
        <!-- disabled for now
        <ul class="nav mt-5 pb-2">

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

          <li class="nav-item px-3 border-left">
            <a v-translate translate-context="Content/TrackShow/Track metadatas tab title" class="nav-link active"
               href="#"
            >Metadata</a>
          </li>
        </ul>-->
        <div class="border-top border-bottom py-4 my-4">
          <div class="row">
            <div class="col-sm-6">
              <h4 v-translate translate-context="Content/TrackShow/Track metadatas headline">
                Metadata of the original file
              </h4>
              <table class="table table-sm my-0">
                <tbody>
                  <tr>
                    <th scope="row" class="col-md-3 border-0 font-weight-normal">
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
                Metadata of the transcoded file
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
      <Sidebar :user="track.account" />
    </div>
  </div>
</template>

<style scoped lang="scss">
span.tags_pill {
  margin-right: 5px;
}
</style>

<script>
import { mapState } from 'vuex'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'
import Sidebar from '../../components/sidebar/sidebar.vue'
import ContentAudioPlayer from '../../components/content_audio_player/content_audio_player.vue'

export default {
  components: {
    Sidebar,
    ContentAudioPlayer
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
    user () {
      return this.$store.getters.findUser(this.userId)
    },
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

    // Fetch track or logs if error
    this.fetchTrack()
      .then((v) => {
        if (!this.trackError && this.track && this.processingDone) {
          // nothing
        } else {
          this.fetchTrackLogs()
        }
      })
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
