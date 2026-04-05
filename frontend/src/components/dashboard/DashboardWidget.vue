<template>
  <div class="dashboard-widget">
    <div class="dashboard-widget__header">
      <slot name="header-drag"></slot>
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
  border-radius: var(--button-border-radius, 12px);
  overflow: hidden;
  box-shadow: var(--floating-box);
  transition:
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.dashboard-widget:hover {
  box-shadow:
    var(--floating-box),
    0 0 20px var(--clr-black-trans-400),
    inset 0 0 8px var(--clr-shadow-highlight-sm);
  transform: translateY(-1px);
}

.dashboard-widget__header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xs) var(--space-xs);
  background: var(--clr-primary--lighter);
  border-bottom: 1px solid var(--clr-gray-700);
  min-height: 2rem;
}

.dashboard-widget__title {
  position: relative;
  z-index: 6;
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  font-size: var(--fs-600);
  color: var(--clr-gray-300);
  pointer-events: none;
}

.dashboard-widget__title a,
.dashboard-widget__title i {
  pointer-events: auto;
}

.dashboard-widget__title i {
  font-size: var(--fs-600);
  color: var(--clr-text);
  filter: drop-shadow(0 0 5px var(--clr-accent));
}

.dashboard-widget__link {
  color: var(--clr-gray-200);
  text-decoration: none;
  font-weight: 600;
  transition:
    color 0.15s ease,
    text-shadow 0.15s ease;
}

.dashboard-widget__link:hover {
  color: var(--clr-accent);
  text-shadow: 0 0 8px var(--clr-accent);
}

.dashboard-widget__remove {
  position: absolute;
  right: var(--space-xs);
  z-index: 6;
  background: var(--clr-gray-800);
  border: 1px solid var(--clr-gray-600);
  color: var(--clr-gray-500);
  cursor: pointer;
  padding: var(--space-3xs);
  font-size: var(--fs-300);
  line-height: 1;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.dashboard-widget__remove:hover {
  color: var(--clr-error);
  border-color: var(--clr-error);
  box-shadow: 0 0 8px var(--clr-error);
  transform: scale(1.2);
}

.dashboard-widget__content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2xs) var(--space-xs);
  font-size: var(--fs-400);
  color-scheme: dark;
  scrollbar-width: thin;
  scrollbar-color: var(--clr-gray-600) var(--clr-gray-900);
}

.dashboard-widget__content::-webkit-scrollbar {
  width: 6px;
}

.dashboard-widget__content::-webkit-scrollbar-track {
  background: var(--clr-gray-900);
}

.dashboard-widget__content::-webkit-scrollbar-thumb {
  background: var(--clr-gray-600);
  border-radius: 3px;
}

.dashboard-widget__content::-webkit-scrollbar-thumb:hover {
  background: var(--clr-gray-500);
}
</style>
