<template>
  <div class="task-layout__info">
    <span class="task-layout__count task--overdue">Overdue Tasks: {{ overdueCount }}</span>
    <span class="task-layout__count task--critical">Critical Tasks: {{ criticalCount }}</span>
    <span class="task-layout__toggle">
      <span
        class="button-toggle-selector left"
        :class="{ pressed: viewType === 'block' }"
      >
        <span
          class="left"
          data-tooltip="block layout"
          data-position="left"
        >
          <button
            v-if="viewType !== 'block'"
            class="button--hidden"
            @click="$emit('update:viewType', 'block')"
          >
            <i class="button-icon fa-solid fa-table-cells-large"></i>
          </button>
          <i
            v-else
            class="button-icon pressed fa-solid fa-table-cells-large"
          ></i>
        </span>
      </span>
      <span
        class="button-toggle-selector right"
        :class="{ pressed: viewType === 'compact' }"
      >
        <span
          class="right"
          data-tooltip="compact layout"
          data-position="right"
        >
          <button
            v-if="viewType !== 'compact'"
            class="button--hidden"
            @click="$emit('update:viewType', 'compact')"
          >
            <i class="button-icon fa-solid fa-bars"></i>
          </button>
          <i
            v-else
            class="button-icon pressed fa-solid fa-bars"
          ></i>
        </span>
      </span>
    </span>
    <span class="task-layout__count task--soon">Due Soon Tasks: {{ dueSoonCount }}</span>
    <span class="task-layout__count task--total">Total Tasks: {{ totalCount }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  overdueCount: number
  criticalCount: number
  dueSoonCount: number
  totalCount: number
  viewType: 'block' | 'compact'
}>()

defineEmits<{
  'update:viewType': [value: 'block' | 'compact']
}>()
</script>

<style scoped>
.task-layout__toggle {
  display: inline-flex;
}
</style>
