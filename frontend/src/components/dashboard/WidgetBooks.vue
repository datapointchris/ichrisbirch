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
        <span>{{ store.statusCounts.unread }} unread</span>
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

const currentlyReading = computed(() => store.books.filter((b) => b.progress === 'reading').slice(0, 6))

onMounted(() => {
  if (store.books.length === 0) store.fetchAll()
})
</script>
