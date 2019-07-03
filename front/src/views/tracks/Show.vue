<template>
  <div>
    <h4>Show track</h4>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  data: () => ({
  }),
  computed: {
    ...mapState({
      signedIn: state => !!state.users.currentUser
    })
  },
  created () {
  },
  methods: {
  }
}
</script>
