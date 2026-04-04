<template>
  <div
    class="stats-table-row"
    :style="gridStyle"
  >
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  columns?: string
  columnCount?: number
}>()

const gridStyle = computed(() => ({
  gridTemplateColumns: props.columns ?? `1fr ${'auto '.repeat((props.columnCount ?? 3) - 1).trim()}`,
}))
</script>

<style scoped>
.stats-table-row {
  display: grid;
  gap: var(--space-m);
  align-items: center;
  padding: var(--space-2xs) var(--space-s);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
}
</style>
