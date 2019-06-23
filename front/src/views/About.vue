<template>
  <div class="about">
    <h2>Welcome on instance: {{ instanceName }}</h2>
    <div>
      <h3>Description</h3>
      {{ instanceDescription }}
    </div>
    <div>
      <h3>Terms of service</h3>
      {{ instanceTos }}
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
      instanceTos: state => state.instance.tos
    })
  }
}
</script>
