<template>
  <div class="grid grid--one-column grid--tight">
    <div class="subnav">
      <div class="subnav__links">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="subnav__link"
          :class="{ 'subnav__link--active': route.path === link.to }"
          :data-testid="link.testId"
        >
          <i
            v-if="link.icon"
            :class="link.icon"
            class="subnav__icon"
          ></i>
          {{ link.label }}
        </RouterLink>
      </div>
      <div
        v-if="$slots.default"
        class="subnav__actions"
      >
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

export interface SubnavLink {
  label: string
  to: string
  testId?: string
  icon?: string
}

defineProps<{
  links: SubnavLink[]
}>()

const route = useRoute()
</script>
