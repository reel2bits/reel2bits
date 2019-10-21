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

      <ContentAudioPlayer v-if="currentTrack" :track="currentTrack" :edit-link="editAlbum"
                          :delete-link="deleteAlbum"
      />

      <!-- genre and tags -->
      <div class="d-flex p-2">
        <div class="p-2">
          <i class="fa fa-folder-o" aria-hidden="true" />
          <translate v-if="!album.genre" translate-context="Content/AlbumShow/Album genre">
            No genre defined
          </translate>
          <template v-else>
            {{ album.genre }}
          </template>
        </div>

        <div class="p-2">
          <i class="fa fa-tags" aria-hidden="true" />
          <template v-if="album.tags.length > 0">
            <b-badge v-for="tag in album.tags" :key="tag" pill
                     class="tags_pill" variant="info"
            >
              {{ tag }}
            </b-badge>
          </template>
          <translate v-else translate-context="Content/AlbumShow/Album tags">
            No tags
          </translate>
        </div>
      </div>

      <div>
        <p>{{ album.description }}</p>
      </div>

      <div>
        <draggable ref="draggable" tag="ul" :list="tracksList"
                   class="list-group"
                   handle=".handle" :disabled="!isOwner"
                   @start="trackListReorderStart"
                   @update="tracksListReordered"
        >
          <li v-for="element in tracksList" :key="element.id" class="list-group-item tracks-list">
            <span class="actions">
              <i v-if="isOwner" class="fa fa-align-justify handle" />
              <i v-if="currentTrack.id == element.id" class="fa fa-play" />
            </span>
            <span class="text" @click.prevent="changeCurrentTrack(element.id)">
              {{ element.title }}
            </span>
            <span class="pull-right">
              {{ element.length.toFixed(2) }}
            </span>
          </li>
        </draggable>
      </div>
    </div>

    <div v-if="album" class="col-md-4 d-flex flex-column">
      <Sidebar :user="album.account" />
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

span.tags_pill {
  margin-right: 5px;
}
</style>

<script>
import { mapState } from 'vuex'
import moment from 'moment'
import Sidebar from '../../components/sidebar/sidebar.vue'
import draggable from 'vuedraggable'
import ContentAudioPlayer from '../../components/content_audio_player/content_audio_player.vue'

export default {
  components: {
    draggable,
    Sidebar,
    ContentAudioPlayer
  },
  data: () => ({
    album: null,
    albumError: null,
    deleteError: null,
    isOwner: false,
    userId: null,
    tracksList: [],
    currentOrder: [],
    currentTrack: null
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
    labels () {
      return {
        titleRss: this.$pgettext('Content/TrackAlbum/Content/RSS links tooltip', 'This album as a Podcast compliant RSS Feed')
      }
    }
  },
  created () {
    const user = this.$store.getters.findUser(this.userName)
    if (user) {
      this.userId = user.id
    } else {
      this.$bvToast.toast(this.$pgettext('Content/TrackAlbum/Toast/Error/Message', 'Not found'), {
        title: this.$pgettext('Content/TrackAlbum/Toast/Error/Title', 'User'),
        autoHideDelay: 5000,
        appendToast: false,
        variant: 'danger'
      })
    }
    this.fetchAlbum()
      .then((album) => {
        // Get the first track and set initial tracks list
        // Reorder by album_order
        this.album.tracks.sort((a, b) => { return a.album_order - b.album_order })
        // Build the reordering list
        this.tracksList = this.album.tracks.map(p => { return { id: p.id, title: p.title, length: p.metadatas.duration } })
        // Get the first
        this.currentTrack = this.album.tracks[0]
        console.log(`elected ${this.currentTrack.album_order} as first item`)
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
    changeCurrentTrack (trackId) {
      console.log(`changing track by id ${trackId}`)
      // Find track
      let track = this.album.tracks.find(t => t.id === trackId)
      if (track) {
        console.log(track)
        this.currentTrack = track
      } else {
        this.$bvToast.toast(null, {
          title: this.$pgettext('Content/Album/Toast/Error/Title', 'Cannot find track.'),
          autoHideDelay: 5000,
          appendToast: false,
          variant: 'danger'
        })
      }
    },
    trackListReorderStart () {
      this.currentOrder = this.$refs.draggable._sortable.toArray()
    },
    tracksListReordered: function (event, originalEvent) {
      if (!this.isOwner) { return false }
      console.log('tracks list have been reordered', this.tracksList)
      this.$store.state.api.backendInteractor.albumReorder({ userId: this.userId || this.userName, albumId: this.albumId, tracksOrder: this.tracksList })
        .then(() => {
          this.$bvToast.toast(this.$pgettext('Content/TrackAlbum/Toast/Error/Message', 'Success'), {
            title: this.$pgettext('Content/TrackAlbum/Toast/Error/Title', 'Track reordering'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'success'
          })
        })
        .catch((evt) => {
          this.$bvToast.toast(this.$pgettext('Content/TrackAlbum/Toast/Error/Message', 'Failed'), {
            title: this.$pgettext('Content/TrackAlbum/Toast/Error/Title', 'Track reordering'),
            autoHideDelay: 5000,
            appendToast: false,
            variant: 'danger'
          })
          this.$refs.draggable._sortable.sort(this.currentOrder)
        })
    }
  }
}
</script>
