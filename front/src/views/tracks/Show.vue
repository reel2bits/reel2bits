<template>
  <div v-if="trackError && !track" class="row justify-content-md-center">
    <div class="col-md-6" />
  </div>
  <div v-else class="row">
    <div class="col-md-8">
      <div class="d-flex my-4">
        <img :src="track.picture_url" class="d-flex mr-3" style="width:112px; height:112px; background: #C8D1F4; ">
        <div class="flex-fill">
          <div class="d-flex">
            <h1 class="flex-fill h3">
              {{ track.title }}
            </h1>
            <div class="d-flex">
              {{ track.uploaded_on }}
            </div>
          </div>
          <div v-if="processingDone" class="d-flex my-2">
            <a href="#" role="button" class="btn btn-play btn-primary d-flex mr-2 align-items-center"
               @click="Play"
            ><i class="fa fa-play" aria-hidden="true" />
            </a>
            <div id="wave" class="flex-fill" />
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
              <span class="text-secondary">04:20</span> <span class="text-muted">04:33</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <p>{{ track.description }}</p>
        <p>Licence: <a :href="track.metadatas.licence.link">{{ track.metadatas.licence.name }}</a></p>
      </div>

      <!-- Tabs -->
      <div>
        <ul class="nav mt-5 pb-2">
          <li class="nav-item pr-3">
            <a class="nav-link" href="#">3 Comments</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">10 Likes</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link" href="#">2 Reposts</a>
          </li>
          <li class="nav-item px-3 border-left">
            <a class="nav-link active" href="#">Meta Data</a>
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
              <img src="https://lastfm-img2.akamaized.net/i/u/770x0/a4c9b3bb4d0443abc3bac418835c66a7.jpg#a4c9b3bb4d0443abc3bac418835c66a7" alt="Downliners Sekt" style="height:96px;">
            </div>
            <div class="align-self-center">
              <h2 class="h2 m-0">
                {{ track.user }}
              </h2>
              <p class="h3 font-weight-normal m-0">
                @alexsleepy <button type="button" class="btn btn-primary btn-sm">
                  Follow
                </button>
              </p>
              <p class="text-muted m-0">
                Follows you
              </p>
            </div>
          </div>
          <p class="card-text">
            FIXME bio
          </p>
          <ul class="nav nav-fill">
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">59</p><p class="m-0">Tracks</p></a>
            </li>
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">5</p><p class="m-0">Albums</p></a>
            </li>
            <li class="nav-item border-right">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">841</p><p class="m-0">Followers</p></a>
            </li>
            <li class="nav-item">
              <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">12</p><p class="m-0">Following</p></a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Footer -->
      <footer class="mt-auto mb-4">
        Powered by <a :href="sourceUrl" target="_blank">reel2bits</a>
      </footer>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'
import WaveSurfer from 'wavesurfer'

export default {
  data: () => ({
    track: null,
    trackError: '',
    processing_done: false,
    isOwner: false
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
    }
  },
  mounted () {
    this.fetchTrack()
      .then((v) => {
        if (!this.trackError && this.track) {
          console.log('initiating wavesurfer')
          this.wavesurfer = WaveSurfer.create({
            container: '#wave',
            height: 40,
            progressColor: '#C728B6',
            waveColor: '#C8D1F4',
            cursorColor: '#313DF2'
          })
          this.wavesurfer.load(this.track.media_transcoded)
        }
      })
  },
  methods: {
    async fetchTrack () {
      console.log('fetching track...')
      try {
        let data = await apiService.trackFetch(this.userName, this.trackId, this.$store)
        this.track = data
        this.processing_done = this.track.processing.done
        this.isOwner = (this.track.user === this.$store.state.users.currentUser.screen_name)
        console.log('track fetched')
      } catch (e) {
        console.log('cannot fetch track:' + e.message)
        this.trackError = e.message
      }
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
    Play: function () {
      this.wavesurfer.playPause()
      // console.log(this.track.media_transcoded)
    }
  }
}
</script>
