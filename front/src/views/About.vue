<template>
  <div class="row justify-content-md-center">
    <div class="col-md-8">
      <h2 v-translate="{instanceName: instanceName}" translate-context="Content/About/Headline/Title">
        Welcome on instance: %{ instanceName }
      </h2>
      <div>
        <h3 v-translate translate-context="Content/About/Headline/Description">
          Description
        </h3>
        {{ instanceDescription }}
      </div>
      <div v-html="instanceTos" />
      <div>
        <h3 v-translate translate-context="Content/About/Headline/VersAndSources">
          Versions and sources
        </h3>
        <translate translate-context="Content/About/Headline/FrontendVersion" :translate-params="{frontVersion: frontVersion}">
          Frontend version: %{ frontVersion }
        </translate><br>
        <translate translate-context="Content/About/Headline/BackendVersion" :translate-params="{backendVersion: backendVersion}">
          Backend version: %{ backendVersion }
        </translate><br>
        <translate translate-context="Content/About/Link/Prefix">
          Source:
        </translate><a :href="sourceUrl" target="_blank">{{ sourceUrl }}</a>
      </div>
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
      frontVersion () { return window.___reel2bitsfe_commit_hash },
      backendVersion: state => state.instance.backendVersion,
      sourceUrl: state => state.instance.sourceUrl
    })
  }
}
</script>
