<template>
  <div class="row justify-content-md-center">
    <div class="col-md-12">
      <h4 v-translate="{username: currentUser.screen_name}" translate-context="Content/Quota(user)/Headline">
        %{ username }'s quota summary
      </h4>
      <b-table show-empty :items="items" :fields="fields"
               :current-page="currentPage" :per-page="0"
      >
        <template v-slot:cell(name)="item">
          <b-link :to="{ name: 'tracks-show', params: { username: currentUser.screen_name, trackId: item.item.slug } }">
            {{ item.value }}
          </b-link>
        </template>

        <template v-slot:cell(fileSize)="item">
          {{ item.value | humanizeSize }}
        </template>

        <template v-slot:cell(transcodeSize)="item">
          {{ item.value | humanizeSize }}
        </template>
      </b-table>
      <b-pagination v-model="currentPage" size="md" :total-rows="totalItems"
                    :per-page="perPage"
      />
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'

export default {
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
      items: [],
      fields: [
        {
          key: 'name',
          label: this.$pgettext('Content/Quota(user)/Table/Heading', 'Track Name')
        },
        {
          key: 'fileSize',
          label: this.$pgettext('Content/Quota(user)/Table/Heading', 'File Size')
        },
        {
          key: 'transcodeSize',
          label: this.$pgettext('Content/Quota(user)/Table/Heading', 'Transcoding Size')
        }
      ],
      currentPage: 1,
      perPage: 20,
      totalItems: 0
    }
  },
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    currentUser () { return this.$store.state.users.currentUser }
  },
  watch: {
    currentPage: {
      handler: function (value) {
        this.fetchQuota().catch(error => {
          console.error(error)
        })
      }
    }
  },
  mounted () {
    this.fetchQuota().catch(error => {
      console.error(error)
    })
  },
  methods: {
    async fetchQuota () {
      try {
        let data = await apiService.fetchUserQuota(this.currentUser.screen_name, this.currentPage, this.perPage, this.$store)
        this.items = data.items
        this.totalItems = data.totalItems
      } catch (e) {
        this.errors = e.message
        this.$bvToast.toast(this.$pgettext('Content/Quota(user)/Toast/Error/Message', 'Error fetching user quota summary'), {
          title: this.$pgettext('Content/Quota(user)/Toast/Error/Title', 'Quota'),
          autoHideDelay: 5000,
          appendToast: false,
          variant: 'danger'
        })
      }
    }
  }
}
</script>
