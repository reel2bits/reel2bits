<template>
  <div>
    <template v-if="currentUser">
      <UserCard :user="currentUser" />
      <template v-if="currentUser.reel2bits.quota_limit > 0">
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
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    humanQuota () {
      let quotaCount = ''
      let quotaLimit = ''

      if (this.currentUser.reel2bits.quota_count === 0) {
        quotaCount = '0'
      } else {
        let ffs = fileSizeFormatService.fileSizeFormat(this.currentUser.reel2bits.quota_count)
        quotaCount = ffs.num + ffs.unit
      }

      if (this.currentUser.reel2bits.quota_limit === 0) {
        quotaLimit = '0'
      } else {
        let ffs = fileSizeFormatService.fileSizeFormat(this.currentUser.reel2bits.quota_limit)
        quotaLimit = ffs.num + ffs.unit
      }

      return quotaCount + '/' + quotaLimit
    }
  }
}

export default Sidebar
</script>
