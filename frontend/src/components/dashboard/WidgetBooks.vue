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
        <span>{{ store.statusCounts.reading }} reading</span>
        <span>{{ store.statusCounts.toRead }} to read</span>
        <span>{{ store.statusCounts.read }} read</span>
      </div>
      <div
        v-for="book in currentlyReading"
        :key="book.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ book.title }}</span>
        <span class="widget-list__meta">{{ book.author }}</span>
      </div>
      <div
        v-if="currentlyReading.length === 0"
        class="widget-empty"
      >
        Not reading anything
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBooksStore } from '@/stores/books'

const store = useBooksStore()

const currentlyReading = computed(() => store.books.filter((b) => b.read_start_date && !b.read_finish_date && !b.abandoned).slice(0, 6))

onMounted(() => {
  if (store.books.length === 0) store.fetchAll()
})
</script>

<style scoped>
.widget-stats {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-2xs);
  border-bottom: 1px solid var(--clr-gray-800);
  margin-bottom: var(--space-2xs);
  color: var(--clr-gray-400);
  font-size: var(--fs-200);
}
</style>
