<template>
  <div>
    <template v-if="displayUser">
      <UserCard :user="displayUser" />

      <template>
        <div class="card mb-4">
          <div class="card-body py-3 px-3">
            <translate translate-context="Content/UserProfile/Sidebar/RSS Feed" :translate-params="{quotaSlashRepr: humanQuota}">
              All user tracks:
            </translate>
            <a :href="displayUser.reel2bits.url_feed" target="_blank"><i class="fa fa-rss" aria-hidden="true" /></a>
          </div>
        </div>
      </template>

      <template v-if="isUs && displayUser.reel2bits.quota_limit > 0">
        <div class="card mb-4">
          <div class="card-body py-3 px-3">
            <translate translate-context="Content/UserProfile/Sidebar/Quota" :translate-params="{quotaSlashRepr: humanQuota}">
              Quota: %{ quotaSlashRepr }
            </translate>
          </div>
        </div>
      </template>
    </template>
    <Footer />
  </div>
</template>

<script>
import UserCard from '../../components/user_card/user_card.vue'
import Footer from '../footer/footer.vue'
import fileSizeFormatService from '../../services/file_size_format/file_size_format.js'

const Sidebar = {
  components: {
    UserCard,
    Footer
  },
  props: [
    'user'
  ],
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    displayUser () { return this.user || this.currentUser },
    isUs () {
      return this.displayUser && this.$store.state.users.currentUser.id &&
        this.displayUser.id === this.$store.state.users.currentUser.id
    },
    humanQuota () {
      let quotaCount = ''
      let quotaLimit = ''

      if (this.displayUser.reel2bits.quota_count === 0) {
        quotaCount = '0'
      } else {
        let ffs = fileSizeFormatService.fileSizeFormat(this.displayUser.reel2bits.quota_count)
        quotaCount = ffs.num + ffs.unit
      }

      if (this.displayUser.reel2bits.quota_limit === 0) {
        quotaLimit = '0'
      } else {
        let ffs = fileSizeFormatService.fileSizeFormat(this.displayUser.reel2bits.quota_limit)
        quotaLimit = ffs.num + ffs.unit
      }

      return quotaCount + '/' + quotaLimit
    }
  }
}

export default Sidebar
</script>
