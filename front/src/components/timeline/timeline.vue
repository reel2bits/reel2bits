<template>
  <div>
    <p class="h3">
      {{ title }}
    </p>
  </div>
</template>

<script>
const Timeline = {
  props: [
    'timeline',
    'timelineName',
    'title'
  ]
}

export default Timeline
</script>
