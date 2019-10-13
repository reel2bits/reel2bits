<template>
  <div v-if="announcement">
    <b-alert show variant="info">
      {{ announcement }}
    </b-alert>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  computed: {
    ...mapState({
      announcement: state => state.instance.announcement
    })
  }
}
</script>
