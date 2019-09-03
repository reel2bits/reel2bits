<template>
  <div>
    <ul class="nav mt-5 pb-2">
      <li class="nav-item pr-3">
        <router-link :to="{ name: 'friends' }"
                     text="Your feed"
                     class="nav-link"
        >
          Your feed
        </router-link>
      </li>
      <li class="nav-item px-3 border-left">
        <router-link :to="{ name: 'public-timeline' }"
                     text="Public"
                     class="nav-link"
        >
          This instance
        </router-link>
      </li>
      <li class="nav-item px-3 border-left">
        <router-link :to="{ name: 'public-external-timeline' }"
                     text="The Whole Known Network"
                     class="nav-link active"
        >
          The Whole Known Network
        </router-link>
      </li>
    </ul>

    <Timeline
      title="The Whole Known Network"
      :timeline-name="'publicAndExternal'"
    />
  </div>
</template>

<script>
import Timeline from '../timeline/timeline.vue'
const PublicAndExternalTimeline = {
  components: {
    Timeline
  }
}

export default PublicAndExternalTimeline
</script>
