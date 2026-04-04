<template>
  <div>
    <ArticlesSubnav />

    <!-- Search Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <form
          class="articles__search"
          @submit.prevent="handleSearch"
        >
          <input
            v-model="searchInput"
            type="text"
            class="textbox"
            placeholder="Search articles by tags (comma-separated)..."
          />
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Search</span>
          </button>
          <button
            v-if="store.isSearchActive"
            type="button"
            class="button button--danger"
            @click="handleClearSearch"
          >
            <span class="button__text button__text--danger">Clear</span>
          </button>
          <button
            data-testid="article-archive-toggle"
            type="button"
            class="button"
            :class="{ 'button--active': store.showArchived }"
            @click="handleToggleShowArchived"
          >
            <span class="button__text">{{ store.showArchived ? 'Show Active' : 'Show Archived' }}</span>
          </button>
        </form>
        <p
          v-if="store.isSearchActive"
          class="articles__search-label"
        >
          Showing results for: {{ store.searchQuery }}
        </p>
      </div>
    </div>

    <!-- Current Article Banner -->
    <div
      v-if="store.currentArticle && !store.isSearchActive"
      class="grid grid--one-column grid--tight"
    >
      <div class="grid__item articles__current">
        <div class="articles__current-label"><i class="fa-solid fa-bookmark"></i> Current Article</div>
        <a
          :href="store.currentArticle.url"
          target="_blank"
          class="articles__current-title"
          >{{ store.currentArticle.title }}</a
        >
        <span class="articles__current-tags">{{ store.currentArticle.tags.join(', ') }}</span>
        <div class="articles__current-actions">
          <button
            class="button"
            @click="handleMarkRead(store.currentArticle!.id)"
          >
            <span class="button__text">Mark Read</span>
          </button>
          <button
            class="button"
            @click="handleRemoveCurrent(store.currentArticle!.id)"
          >
            <span class="button__text">Remove Current</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Article Table -->
    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="articles__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div class="articles__header">
            <span>Title</span>
            <span>Tags</span>
            <span>Saved</span>
            <span>Reads</span>
            <span>Actions</span>
          </div>

          <div
            v-if="store.displayedArticles.length === 0"
            class="articles__empty"
          >
            {{ store.isSearchActive ? 'No articles match your search.' : 'No articles yet.' }}
          </div>

          <template
            v-for="article in store.displayedArticles"
            :key="article.id"
          >
            <div
              data-testid="article-item"
              class="articles__row"
              :class="{
                'articles__row--favorite': article.is_favorite,
                'articles__row--current': article.is_current,
              }"
            >
              <span
                class="articles__title"
                :title="article.title"
              >
                <a
                  :href="article.url"
                  target="_blank"
                  >{{ article.title }}</a
                >
              </span>
              <span class="articles__tags">{{ article.tags.join(', ') }}</span>
              <span>{{ formatDate(article.save_date, 'shortDate') }}</span>
              <span>{{ article.read_count }}</span>
              <span class="articles__actions">
                <i
                  data-testid="article-favorite-button"
                  class="button-icon articles__star fa-solid fa-star"
                  :class="{ 'articles__star--active': article.is_favorite }"
                  title="Toggle favorite"
                  @click="handleToggleFavorite(article.id)"
                ></i>
                <i
                  data-testid="article-edit-button"
                  class="button-icon articles__chevron fa-solid fa-pen-to-square"
                  title="Edit article"
                  @click="openEdit(article)"
                ></i>
                <i
                  data-testid="article-expand-button"
                  class="button-icon articles__chevron fa-solid fa-chevron-down"
                  :class="{ 'articles__chevron--open': expandedId === article.id }"
                  @click="toggleExpand(article.id)"
                ></i>
                <button
                  data-testid="article-delete-button"
                  class="button--hidden"
                  @click="handleDelete(article.id)"
                >
                  <i class="button-icon danger fa-regular fa-trash-can"></i>
                </button>
              </span>
            </div>

            <!-- Expanded Detail -->
            <div
              class="articles__detail"
              :class="{ 'articles__detail--open': expandedId === article.id }"
            >
              <div
                v-if="article.summary"
                class="articles__detail-field"
              >
                <span class="articles__detail-label">Summary</span>
                <span class="articles__detail-value">{{ article.summary }}</span>
              </div>
              <div
                v-if="article.notes"
                class="articles__detail-field"
              >
                <span class="articles__detail-label">Notes</span>
                <span class="articles__detail-value">{{ article.notes }}</span>
              </div>
              <div class="articles__detail-field">
                <span class="articles__detail-label">URL</span>
                <span class="articles__detail-value">
                  <a
                    :href="article.url"
                    target="_blank"
                    >{{ article.url }}</a
                  >
                </span>
              </div>
              <div
                v-if="article.last_read_date"
                class="articles__detail-field"
              >
                <span class="articles__detail-label">Last Read</span>
                <span class="articles__detail-value">{{ formatDate(article.last_read_date, 'shortDate') }}</span>
              </div>
              <div
                v-if="article.review_days"
                class="articles__detail-field"
              >
                <span class="articles__detail-label">Review Days</span>
                <span class="articles__detail-value">{{ article.review_days }}</span>
              </div>
              <div class="articles__detail-actions">
                <button
                  class="button"
                  @click="handleToggleFavorite(article.id)"
                >
                  <span class="button__text">{{ article.is_favorite ? 'Unfavorite' : 'Favorite' }}</span>
                </button>
                <button
                  v-if="article.is_current"
                  class="button"
                  @click="handleRemoveCurrent(article.id)"
                >
                  <span class="button__text">Remove Current</span>
                </button>
                <button
                  v-else
                  class="button"
                  @click="handleMakeCurrent(article.id)"
                >
                  <span class="button__text">Make Current</span>
                </button>
                <button
                  class="button"
                  @click="handleMarkRead(article.id)"
                >
                  <span class="button__text">Mark Read</span>
                </button>
                <button
                  class="button"
                  @click="handleToggleArchive(article.id)"
                >
                  <span class="button__text">{{ article.is_archived ? 'Unarchive' : 'Archive' }}</span>
                </button>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>

    <AddEditArticleModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Article, ArticleUpdate } from '@/api/client'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'
import AddEditArticleModal from '@/components/articles/AddEditArticleModal.vue'
import { formatDate } from '@/composables/formatDate'

const store = useArticlesStore()
const { show: notify } = useNotifications()
const searchInput = ref('')
const expandedId = ref<number | null>(null)
const showModal = ref(false)
const editTarget = ref<{
  id: number
  title: string
  url: string
  tags: string[]
  summary: string
  notes?: string
} | null>(null)

onMounted(() => {
  store.fetchAll()
  store.fetchCurrent()
})

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

function openEdit(article: Article) {
  editTarget.value = {
    id: article.id,
    title: article.title,
    url: article.url,
    tags: article.tags,
    summary: article.summary,
    notes: article.notes,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleUpdate(id: number, data: ArticleUpdate) {
  try {
    await store.update(id, data)
    notify('Article updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update article: ${detail}`, 'error')
  }
}

async function handleToggleFavorite(id: number) {
  try {
    await store.toggleFavorite(id)
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to toggle favorite: ${detail}`, 'error')
  }
}

async function handleToggleArchive(id: number) {
  try {
    await store.toggleArchive(id)
    notify('Article archive status changed', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to toggle archive: ${detail}`, 'error')
  }
}

async function handleMakeCurrent(id: number) {
  try {
    await store.makeCurrent(id)
    notify('Article set as current', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to set current: ${detail}`, 'error')
  }
}

async function handleRemoveCurrent(id: number) {
  try {
    await store.removeCurrent(id)
    notify('Current status removed', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to remove current: ${detail}`, 'error')
  }
}

async function handleMarkRead(id: number) {
  try {
    await store.markRead(id)
    notify('Article marked as read and archived', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to mark as read: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    notify('Article deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete article: ${detail}`, 'error')
  }
}

async function handleSearch() {
  if (!searchInput.value.trim()) return
  try {
    await store.search(searchInput.value.trim())
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Search failed: ${detail}`, 'error')
  }
}

async function handleClearSearch() {
  searchInput.value = ''
  await store.clearSearch()
}

async function handleToggleShowArchived() {
  await store.setShowArchived(!store.showArchived)
}
</script>
