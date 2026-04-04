<template>
  <div class="stats-table">
    <h3 class="stats-table__title">
      <slot name="title"></slot>
    </h3>
    <div
      v-if="empty"
      class="stats-table__empty"
    >
      <slot name="empty"> No data. </slot>
    </div>
    <template v-else>
      <div
        class="stats-table__header"
        :style="gridStyle"
      >
        <span
          v-for="header in headers"
          :key="header"
          >{{ header }}</span
        >
      </div>
      <slot></slot>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  headers: string[]
  columns?: string
  empty?: boolean
}>()

const gridStyle = computed(() => ({
  gridTemplateColumns: props.columns ?? `1fr ${'auto '.repeat(props.headers.length - 1).trim()}`,
}))
</script>

<style scoped>
.stats-table {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
}

.stats-table__title {
  font-size: var(--fs-500);
  color: var(--clr-gray-300);
  margin-bottom: var(--space-xs);
}

.stats-table__header {
  display: grid;
  gap: var(--space-m);
  align-items: center;
  padding: var(--space-2xs) var(--space-s);
  font-size: var(--fs-300);
  color: var(--clr-gray-500);
  border-bottom: 1px solid var(--clr-gray-700);
}

.stats-table__empty {
  color: var(--clr-gray-500);
  font-style: italic;
}
</style>
