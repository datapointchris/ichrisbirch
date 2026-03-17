<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div
        v-if="store.currentArticle"
        class="widget-list__item widget-list__item--highlight"
      >
        <span class="widget-list__name">{{ store.currentArticle.title }}</span>
        <button
          class="widget-action-btn"
          title="Mark as read"
          @click="store.markRead(store.currentArticle!.id)"
        >
          ✓
        </button>
      </div>
      <div
        v-for="article in recentArticles"
        :key="article.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ article.title }}</span>
        <span class="widget-list__meta">{{ article.read_count }}×</span>
      </div>
      <div
        v-if="!store.currentArticle && store.articles.length === 0"
        class="widget-empty"
      >
        No articles
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useArticlesStore } from '@/stores/articles'

const store = useArticlesStore()

const recentArticles = computed(() => store.sortedArticles.filter((a) => !a.is_current && !a.is_archived).slice(0, 5))

onMounted(async () => {
  if (store.articles.length === 0) await store.fetchAll()
  if (!store.currentArticle) await store.fetchCurrent()
})
</script>
