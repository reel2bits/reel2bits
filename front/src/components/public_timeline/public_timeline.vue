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
                     class="nav-link active"
        >
          This instance
        </router-link>
      </li>
      <li class="nav-item px-3 border-left">
        <router-link :to="{ name: 'public-external-timeline' }"
                     text="The Whole Known Network"
                     class="nav-link"
        >
          The Whole Known Network
        </router-link>
      </li>
    </ul>

    <Timeline
      title="Public Timeline"
      timeline-name="public"
    />
  </div>
</template>

<script>
import Timeline from '../timeline/timeline.vue'
const PublicTimeline = {
  components: {
    Timeline
  }
}

export default PublicTimeline
</script>
