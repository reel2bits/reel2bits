<template>
  <footer class="text-center">
    <div class="row justify-content-around">
      <div class="col-md-3 text-truncate">
        {{ url }}
      </div>
      <div class="col-md-3">
        About
      </div>
    </div>
    <div class="row justify-content-around">
      <div class="col-md-3">
        <router-link to="/about">
          About
        </router-link>
      </div>
      <div class="col-md-3">
        <a :href="sourceUrl" target="_blank">Source code</a>
      </div>
    </div>
  </footer>
</template>

<script>
import { mapState } from 'vuex'
export default {
  computed: {
    ...mapState({
      sourceUrl: state => state.instance.sourceUrl
    }),
    url () {
      return window.location.hostname
    }
  }
}
</script>
