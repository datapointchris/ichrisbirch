<template>
  <div>
    <ArticlesSubnav active="articles" />

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
              <span>{{ formatDate(article.save_date) }}</span>
              <span>{{ article.read_count }}</span>
              <span class="articles__actions">
                <i
                  class="button-icon articles__star fa-solid fa-star"
                  :class="{ 'articles__star--active': article.is_favorite }"
                  title="Toggle favorite"
                  @click="handleToggleFavorite(article.id)"
                ></i>
                <i
                  class="button-icon articles__chevron fa-solid fa-chevron-down"
                  :class="{ 'articles__chevron--open': expandedId === article.id }"
                  @click="toggleExpand(article.id)"
                ></i>
                <button
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
                <span class="articles__detail-value">{{ formatDate(article.last_read_date) }}</span>
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

    <!-- Add Article Form -->
    <div class="add-item-wrapper">
      <h2>Add New Article</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleAdd"
      >
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="url">URL:</label>
          <div class="articles__url-row">
            <input
              id="url"
              v-model="form.url"
              type="url"
              class="textbox"
              name="url"
              required
            />
            <button
              type="button"
              class="button"
              :disabled="!form.url.trim() || store.summarizing"
              @click="handleAutoPopulate"
            >
              <span class="button__text">{{ store.summarizing ? 'Summarizing...' : 'Auto Populate' }}</span>
            </button>
          </div>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="title">Title:</label>
          <input
            id="title"
            v-model="form.title"
            type="text"
            class="textbox"
            name="title"
            required
          />
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="tags">Tags (comma-separated):</label>
          <input
            id="tags"
            v-model="form.tags"
            type="text"
            class="textbox"
            name="tags"
          />
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="summary">Summary:</label>
          <textarea
            id="summary"
            v-model="form.summary"
            rows="6"
            class="textbox"
            name="summary"
            required
          ></textarea>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="notes">Notes:</label>
          <textarea
            id="notes"
            v-model="form.notes"
            rows="3"
            class="textbox"
            name="notes"
          ></textarea>
        </div>
        <div class="add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Article</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'

const store = useArticlesStore()
const { show: notify } = useNotifications()
const searchInput = ref('')
const expandedId = ref<number | null>(null)

const form = reactive({
  url: '',
  title: '',
  tags: '',
  summary: '',
  notes: '',
})

onMounted(() => {
  store.fetchAll()
  store.fetchCurrent()
})

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function resetForm() {
  form.url = ''
  form.title = ''
  form.tags = ''
  form.summary = ''
  form.notes = ''
}

async function handleAutoPopulate() {
  if (!form.url.trim()) return
  try {
    const result = await store.summarizeUrl(form.url.trim())
    form.title = result.title
    form.summary = result.summary
    form.tags = result.tags.join(', ')
    notify('Article info populated from URL', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Auto-populate failed: ${detail}`, 'error')
  }
}

async function handleAdd() {
  if (!form.url.trim() || !form.title.trim() || !form.summary.trim()) return
  const tags = form.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  try {
    await store.create({
      url: form.url.trim(),
      title: form.title.trim(),
      tags,
      summary: form.summary.trim(),
      notes: form.notes.trim() || undefined,
      save_date: new Date().toISOString(),
    })
    notify('Article added', 'success')
    resetForm()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add article: ${detail}`, 'error')
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
</script>

<style scoped>
/* Search */
.articles__search {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.articles__search .textbox {
  flex: 1;
}

.articles__search-label {
  margin-top: var(--space-xs);
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  font-style: italic;
}

/* Current Article Banner */
.articles__current {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.articles__current-label {
  font-size: var(--fs-300);
  color: var(--clr-primary-400);
  font-weight: bold;
  white-space: nowrap;
}

.articles__current-title {
  font-size: var(--fs-500);
  font-weight: bold;
  color: inherit;
  text-decoration: none;
}

.articles__current-title:hover {
  text-decoration: underline;
}

.articles__current-tags {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  flex: 1;
}

.articles__current-actions {
  display: flex;
  gap: var(--space-xs);
  margin-left: auto;
}

/* Table header and rows — mirrors books__ pattern */
.articles__header {
  display: grid;
  grid-template-columns: 3fr 2fr 1fr 0.5fr 1fr;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-s);
  border-bottom: 2px solid var(--clr-primary-400);
  font-weight: bold;
  color: var(--clr-gray-200);
}

.articles__row {
  display: grid;
  grid-template-columns: 3fr 2fr 1fr 0.5fr 1fr;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-s);
  border-bottom: 1px solid var(--clr-gray-800);
  align-items: center;
  transition: background-color 0.15s;
}

.articles__row:hover {
  background-color: var(--clr-gray-900);
}

.articles__row--favorite {
  border-left: 3px solid var(--clr-primary-400);
}

.articles__row--current {
  background-color: color-mix(in srgb, var(--clr-primary-400) 8%, transparent);
}

.articles__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.articles__title a {
  color: inherit;
  text-decoration: none;
}

.articles__title a:hover {
  text-decoration: underline;
}

.articles__tags {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
}

.articles__actions {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.articles__star {
  cursor: pointer;
  color: var(--clr-gray-600);
  transition: color 0.15s;
}

.articles__star:hover {
  color: var(--clr-primary-400);
}

.articles__star--active {
  color: var(--clr-primary-400);
}

.articles__chevron {
  cursor: pointer;
  transition: transform 0.2s;
  color: var(--clr-gray-400);
}

.articles__chevron:hover {
  color: var(--clr-gray-200);
}

.articles__chevron--open {
  transform: rotate(180deg);
}

.articles__empty {
  padding: var(--space-m) var(--space-s);
  color: var(--clr-gray-400);
}

/* Expandable detail panel */
.articles__detail {
  display: none;
  padding: var(--space-s) var(--space-m);
  background-color: var(--clr-gray-900);
  border-bottom: 1px solid var(--clr-gray-800);
}

.articles__detail--open {
  display: block;
}

.articles__detail-field {
  margin-bottom: var(--space-xs);
}

.articles__detail-label {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  font-weight: bold;
  display: block;
  margin-bottom: var(--space-3xs);
}

.articles__detail-value {
  display: block;
  word-break: break-word;
}

.articles__detail-value a {
  color: var(--clr-primary-400);
}

.articles__detail-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-s);
  flex-wrap: wrap;
}

/* Form URL row */
.articles__url-row {
  display: flex;
  gap: var(--space-xs);
}

.articles__url-row .textbox {
  flex: 1;
}
</style>
