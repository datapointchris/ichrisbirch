<template>
  <div class="dashboard-widget">
    <div class="dashboard-widget__header">
      <div class="dashboard-widget__title">
        <i :class="icon"></i>
        <RouterLink
          :to="linkTo"
          class="dashboard-widget__link"
        >
          {{ title }}
        </RouterLink>
      </div>
      <button
        v-if="editing"
        class="dashboard-widget__remove"
        title="Remove widget"
        @click="$emit('remove')"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>
    <div class="dashboard-widget__content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  title: string
  icon: string
  linkTo: string
  editing: boolean
}>()

defineEmits<{
  remove: []
}>()
</script>

<style scoped>
.dashboard-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--clr-primary);
  border-radius: 0.5rem;
  overflow: hidden;
}

.dashboard-widget__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3xs) var(--space-xs);
  background: var(--clr-primary--lighter);
  border-bottom: 1px solid var(--clr-gray-700);
  min-height: 2rem;
}

.dashboard-widget__title {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  font-size: var(--fs-200);
  color: var(--clr-gray-300);
}

.dashboard-widget__title i {
  font-size: var(--fs-200);
  color: var(--clr-accent);
}

.dashboard-widget__link {
  color: var(--clr-gray-200);
  text-decoration: none;
  font-weight: 600;
}

.dashboard-widget__link:hover {
  color: var(--clr-accent);
}

.dashboard-widget__remove {
  background: none;
  border: none;
  color: var(--clr-gray-500);
  cursor: pointer;
  padding: var(--space-3xs);
  font-size: var(--fs-300);
  line-height: 1;
}

.dashboard-widget__remove:hover {
  color: var(--clr-accent--red);
}

.dashboard-widget__content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2xs) var(--space-xs);
  font-size: var(--fs-200);
}
</style>
