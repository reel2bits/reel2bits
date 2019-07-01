<template>
  <div class="about">
    <h2>Welcome on instance: {{ instanceName }}</h2>
    <div>
      <h3>Description</h3>
      {{ instanceDescription }}
    </div>
    <div v-html="instanceTos"></div>
    <div>
      <h3>Versions and sources</h3>
      Frontend version: {{ frontVersion }}<br />
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  computed: {
    ...mapState({
      instanceName: state => state.instance.name,
      instanceDescription: state => state.instance.description,
      instanceTos: state => state.instance.tos,
      frontVersion () { return window.___reel2bitsfe_commit_hash }
    })
  }
}
</script>
