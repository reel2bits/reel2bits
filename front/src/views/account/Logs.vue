<template>
  <div class="row justify-content-md-center">
    <div class="col-md-12">
      <h4>{{ currentUser.screen_name }}'s logs</h4>
      <b-table show-empty :items="items" :fields="fields"
               :current-page="currentPage" :per-page="0"
      />
      <b-pagination v-model="currentPage" size="md" :total-rows="totalItems"
                    :per-page="perPage"
      />
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../../services/api/api.service.js'

export default {
  data: () => ({
    items: [],
    fields: [
      {
        key: 'date',
        label: 'Date'
      },
      {
        key: 'category',
        label: 'Category'
      },
      {
        key: 'level',
        label: 'Level'
      },
      {
        key: 'itemId',
        label: 'Item ID'
      },
      {
        key: 'message',
        label: 'Message'
      }
    ],
    currentPage: 0,
    perPage: 20,
    totalItems: 0
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    }),
    currentUser () { return this.$store.state.users.currentUser }
  },
  watch: {
    currentPage: {
      handler: function (value) {
        this.fetchLogs().catch(error => {
          console.error(error)
        })
      }
    }
  },
  mounted () {
    this.fetchLogs().catch(error => {
      console.error(error)
    })
  },
  methods: {
    async fetchLogs () {
      try {
        let data = await apiService.fetchUserLogs(this.currentUser.screen_name, this.currentPage, this.perPage, this.$store)
        this.items = data.items
        this.totalItems = data.totalItems
      } catch (e) {
        this.errors = e.message
      }
    }
  }
}
</script>
