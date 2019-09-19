<template>
  <footer class="text-center">
    <div class="row justify-content-around">
      <div class="col-md-4 text-truncate" :title="url">
        {{ url }}
      </div>
      <div class="col-md-4">
        <translate translate-context="Footer/*/Link/About">
          About
        </translate>
      </div>
    </div>
    <div class="row justify-content-around">
      <div class="col-md-4">
        <router-link to="/about">
          <translate translate-context="Footer/*/Link/AboutThisInstance">
            About this instance
          </translate>
        </router-link>
      </div>
      <div class="col-md-4">
        <a :href="sourceUrl" target="_blank"><translate translate-context="Footer/*/Link/SourceCode">Source code</translate></a>
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
