<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div class="widget-stats">
        <span class="widget-stats__total widget-stats__total--red">${{ store.totalWasted.toFixed(2) }}</span>
        <span>total wasted</span>
      </div>
      <div
        v-for="item in recentItems"
        :key="item.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ item.item }}</span>
        <span class="widget-list__meta">${{ item.amount.toFixed(2) }}</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useMoneyWastedStore } from '@/stores/moneyWasted'

const store = useMoneyWastedStore()

const recentItems = computed(() => store.sortedItems.slice(0, 6))

onMounted(() => {
  if (store.items.length === 0) store.fetchAll()
})
</script>
