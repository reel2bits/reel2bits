// File imported from https://git.pleroma.social/pleroma/pleroma-fe/blob/develop/src/components/oauth_callback/oauth_callback.js
import oauth from '../../backend/oauth/oauth.js'

const oac = {
  props: ['code'],
  mounted () {
    console.log('/oauth-callback got called')
    if (this.code) {
      console.log('with a code ! ' + this.code)
      const { clientId, clientSecret } = this.$store.state.oauth

      oauth.getToken({
        clientId,
        clientSecret,
        instance: this.$store.state.instance.server,
        code: this.code
      }).then((result) => {
        this.$store.commit('setToken', result.access_token)
        this.$store.dispatch('loginUser', result.access_token)
        this.$router.push({ name: 'profile' })
      })
    }
  }
}

export default oac
