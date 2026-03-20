<template>
  <div>
    <!-- Info Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="task-layout__info">
        <span
          class="task-layout__count book--read book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'read' }"
          @click="store.setFilter('read')"
          >Read: {{ store.statusCounts.read }}</span
        >
        <span
          class="task-layout__count book--reading book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'reading' }"
          @click="store.setFilter('reading')"
          >Reading: {{ store.statusCounts.reading }}</span
        >
        <span
          class="task-layout__count book--unread book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'unread' }"
          @click="store.setFilter('unread')"
          >Unread: {{ store.statusCounts.unread }}</span
        >
        <span
          class="task-layout__count book--abandoned book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'abandoned' }"
          @click="store.setFilter('abandoned')"
          >Abandoned: {{ store.statusCounts.abandoned }}</span
        >
        <span
          class="task-layout__count book--total book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'all' }"
          @click="store.setFilter('all')"
          >Total: {{ store.statusCounts.total }}</span
        >
        <select
          class="textbox books__filter-select"
          :value="store.activeFilter"
          @change="store.setFilter(($event.target as HTMLSelectElement).value)"
        >
          <option value="all">All Progress</option>
          <option
            v-for="(label, value) in statusLabels"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
        <select
          class="textbox books__filter-select"
          :value="store.ownershipFilter"
          @change="store.setOwnershipFilter(($event.target as HTMLSelectElement).value)"
        >
          <option value="all">All Ownership</option>
          <option
            v-for="(label, value) in ownershipLabels"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <form
          class="books__search"
          @submit.prevent="handleSearch"
        >
          <input
            v-model="searchInput"
            type="text"
            class="textbox"
            placeholder="Search books (comma-separated terms)..."
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
          class="books__search-label"
        >
          Showing results for: {{ store.searchQuery }}
        </p>
      </div>
    </div>

    <!-- Book Table -->
    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="books__empty-message"
          style="display: block"
        >
          Loading...
        </div>
        <template v-else>
          <div class="books__header">
            <span
              class="books__sortable"
              @click="store.setSort('title')"
              >Title<span class="books__sort-indicator">{{ sortIndicator('title') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('author')"
              >Author<span class="books__sort-indicator">{{ sortIndicator('author') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('priority')"
              >Priority<span class="books__sort-indicator">{{ sortIndicator('priority') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('progress')"
              >Progress<span class="books__sort-indicator">{{ sortIndicator('progress') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('ownership')"
              >Ownership<span class="books__sort-indicator">{{ sortIndicator('ownership') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('rating')"
              >Rating<span class="books__sort-indicator">{{ sortIndicator('rating') }}</span></span
            >
            <span>Actions</span>
          </div>

          <template v-if="store.sortedBooks.length === 0">
            <div
              class="books__empty-message"
              style="display: block"
            >
              No books match the selected filter.
            </div>
          </template>

          <template
            v-for="book in store.sortedBooks"
            :key="book.id"
          >
            <div
              data-testid="book-item"
              class="books__row"
              :class="`book--${book.progress}`"
            >
              <span
                class="books__title"
                :title="book.title"
                >{{ book.title }}</span
              >
              <span>{{ book.author }}</span>
              <span>{{ book.priority ?? '' }}</span>
              <span>{{ statusLabels[book.progress as BookProgress] }}</span>
              <span>{{ ownershipLabels[book.ownership as BookOwnership] ?? book.ownership }}</span>
              <span>{{ book.rating ?? '' }}</span>
              <span class="books__actions">
                <i
                  class="button-icon books__chevron fa-solid fa-chevron-down"
                  :class="{ 'books__chevron--open': expandedBookId === book.id }"
                  @click="toggleDetail(book.id)"
                ></i>
                <i
                  data-testid="book-edit-button"
                  class="button-icon warning fa-solid fa-pen-to-square"
                  @click="openEdit(book)"
                ></i>
                <button
                  data-testid="book-delete-button"
                  class="button--hidden"
                  @click="handleDelete(book.id)"
                >
                  <i class="button-icon danger fa-regular fa-trash-can"></i>
                </button>
              </span>
            </div>

            <div
              class="books__detail"
              :class="{ 'books__detail--open': expandedBookId === book.id }"
            >
              <div
                v-if="book.isbn"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">ISBN</span>
                <span class="books__detail-field-value">{{ book.isbn }}</span>
              </div>
              <div class="books__detail-field">
                <span class="books__detail-field-label">Tags</span>
                <span class="books__detail-field-value">{{ book.tags.join(', ') }}</span>
              </div>
              <div
                v-if="book.goodreads_url"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Goodreads</span>
                <span class="books__detail-field-value">
                  <a
                    :href="book.goodreads_url"
                    target="_blank"
                    class="books__link"
                    >View on Goodreads</a
                  >
                </span>
              </div>
              <div
                v-if="book.priority"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Priority</span>
                <span class="books__detail-field-value">{{ book.priority }}</span>
              </div>
              <div
                v-if="book.purchase_date"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Purchase Date</span>
                <span class="books__detail-field-value">{{ formatDate(book.purchase_date) }}</span>
              </div>
              <div
                v-if="book.purchase_price"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Purchase Price</span>
                <span class="books__detail-field-value">{{ formatPrice(book.purchase_price) }}</span>
              </div>
              <div
                v-if="book.sell_date"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Sell Date</span>
                <span class="books__detail-field-value">{{ formatDate(book.sell_date) }}</span>
              </div>
              <div
                v-if="book.sell_price"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Sell Price</span>
                <span class="books__detail-field-value">{{ formatPrice(book.sell_price) }}</span>
              </div>
              <div
                v-if="book.read_start_date"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Read Start Date</span>
                <span class="books__detail-field-value">{{ formatDate(book.read_start_date) }}</span>
              </div>
              <div class="books__detail-field">
                <span class="books__detail-field-label">Ownership</span>
                <span class="books__detail-field-value">{{ ownershipLabels[book.ownership as BookOwnership] ?? book.ownership }}</span>
              </div>
              <div
                v-if="book.location"
                class="books__detail-field"
              >
                <span class="books__detail-field-label">Location</span>
                <span class="books__detail-field-value">{{ book.location }}</span>
              </div>
              <div
                v-if="book.notes"
                class="books__detail-field books__detail-notes"
              >
                <span class="books__detail-field-label">Notes</span>
                <span class="books__detail-field-value">{{ book.notes }}</span>
              </div>
              <div
                v-if="book.review"
                class="books__detail-field books__detail-notes"
              >
                <span class="books__detail-field-label">Review</span>
                <span class="books__detail-field-value">{{ book.review }}</span>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="book-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Book</span>
      </button>
    </div>

    <AddEditBookModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBooksStore } from '@/stores/books'
import type { BookProgress, BookOwnership } from '@/stores/books'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Book } from '@/api/client'
import AddEditBookModal from '@/components/books/AddEditBookModal.vue'

const store = useBooksStore()
const { show: notify } = useNotifications()

const expandedBookId = ref<number | null>(null)
const searchInput = ref('')
const showModal = ref(false)
const editTarget = ref<Book | null>(null)

const statusLabels: Record<BookProgress, string> = {
  unread: 'Unread',
  reading: 'Reading',
  read: 'Read',
  abandoned: 'Abandoned',
}

const ownershipLabels: Record<BookOwnership, string> = {
  owned: 'Owned',
  to_purchase: 'To Purchase',
  rejected: 'Rejected',
  sold: 'Sold',
  donated: 'Donated',
}

onMounted(() => {
  store.fetchAll()
})

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(date)
}

function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}

function sortIndicator(field: string): string {
  if (store.sortField !== field) return ''
  return store.sortDirection === 'asc' ? ' \u25B2' : ' \u25BC'
}

function toggleDetail(bookId: number) {
  expandedBookId.value = expandedBookId.value === bookId ? null : bookId
}

async function handleDelete(id: number) {
  const book = store.books.find((b) => b.id === id)
  const label = book ? `${book.title}: ${book.author}` : `Book ${id}`
  try {
    await store.remove(id)
    notify(`${label} | deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`${label} | delete failed: ${detail}`, 'error')
  }
}

function openEdit(book: Book) {
  editTarget.value = book
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: Parameters<typeof store.create>[0]) {
  try {
    await store.create(data)
    notify(`${data.title}: ${data.author} | added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`${data.title}: ${data.author} | add failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: Parameters<typeof store.update>[1]) {
  try {
    await store.update(id, data)
    notify('Book updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
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
.books__search {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.books__search .textbox {
  flex: 1;
}

.books__search-label {
  margin-top: var(--space-xs);
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  font-style: italic;
}

.books__filter-select {
  width: auto;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-300);
}
</style>
