<template>
  <div
    class="button-submit-issue"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
  >
    <div class="button-submit-issue__text">
      <span class="fa-solid fa-bug"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  click: []
}>()
</script>

<style scoped></style>
