<template>
  <div class="grid grid--one-column grid--tight">
    <div class="articles-subnav">
      <div class="articles-subnav__links">
        <RouterLink
          to="/articles"
          class="articles-subnav__link"
          :class="{ 'articles-subnav__link--active': active === 'articles' }"
        >
          All Articles
        </RouterLink>
        <RouterLink
          to="/articles/bulk-import"
          class="articles-subnav__link"
          :class="{ 'articles-subnav__link--active': active === 'bulk-import' }"
        >
          Bulk Import
        </RouterLink>
        <RouterLink
          to="/articles/insights"
          class="articles-subnav__link"
          :class="{ 'articles-subnav__link--active': active === 'insights' }"
        >
          Insights
        </RouterLink>
        <RouterLink
          to="/articles/stats"
          class="articles-subnav__link"
          :class="{ 'articles-subnav__link--active': active === 'stats' }"
        >
          Stats
        </RouterLink>
      </div>
      <div class="articles-subnav__actions">
        <button
          data-testid="article-add-button"
          class="button"
          @click="showModal = true"
        >
          <span class="button__text">Add Article</span>
        </button>
      </div>
    </div>
  </div>

  <AddEditArticleModal
    :visible="showModal"
    :edit-data="null"
    @close="showModal = false"
    @create="handleCreate"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { ArticleCreate } from '@/api/client'
import AddEditArticleModal from '@/components/articles/AddEditArticleModal.vue'

defineProps<{
  active: 'articles' | 'bulk-import' | 'insights' | 'stats'
}>()

const store = useArticlesStore()
const { show: notify } = useNotifications()
const showModal = ref(false)

async function handleCreate(data: ArticleCreate) {
  try {
    await store.create(data)
    notify('Article added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add article: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.articles-subnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.articles-subnav__links {
  display: flex;
  gap: var(--space-s);
  align-items: center;
}

.articles-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.articles-subnav__link:hover {
  color: var(--clr-primary-400);
}

.articles-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
