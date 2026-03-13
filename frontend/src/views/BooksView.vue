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
          class="task-layout__count book--to-read book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'to-read' }"
          @click="store.setFilter('to-read')"
          >To Read: {{ store.statusCounts.toRead }}</span
        >
        <span
          class="task-layout__count book--abandoned book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'abandoned' }"
          @click="store.setFilter('abandoned')"
          >Abandoned: {{ store.statusCounts.abandoned }}</span
        >
        <span
          class="task-layout__count book--sold book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'sold' }"
          @click="store.setFilter('sold')"
          >Sold: {{ store.statusCounts.sold }}</span
        >
        <span
          class="task-layout__count book--total book-filter"
          :class="{ 'book-filter--active': store.activeFilter === 'all' }"
          @click="store.setFilter('all')"
          >Total: {{ store.statusCounts.total }}</span
        >
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
            <span>Status</span>
            <span
              class="books__sortable"
              @click="store.setSort('rating')"
              >Rating<span class="books__sort-indicator">{{ sortIndicator('rating') }}</span></span
            >
            <span
              class="books__sortable"
              @click="store.setSort('finished')"
              >Finished<span class="books__sort-indicator">{{ sortIndicator('finished') }}</span></span
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
              class="books__row"
              :class="`book--${deriveStatus(book)}`"
            >
              <span
                class="books__title"
                :title="book.title"
                >{{ book.title }}</span
              >
              <span>{{ book.author }}</span>
              <span
                ><span :class="`books__status-badge task-layout__count book--${deriveStatus(book)}`">{{
                  statusLabels[deriveStatus(book)]
                }}</span></span
              >
              <span>{{ book.rating ?? '' }}</span>
              <span>{{ book.read_finish_date ? formatDate(book.read_finish_date) : '' }}</span>
              <span class="books__actions">
                <i
                  class="button-icon books__chevron fa-solid fa-chevron-down"
                  :class="{ 'books__chevron--open': expandedBookId === book.id }"
                  @click="toggleDetail(book.id)"
                ></i>
                <i
                  class="button-icon warning fa-solid fa-pen-to-square"
                  @click="startEdit(book)"
                ></i>
                <button
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
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Add/Edit Form -->
    <div class="add-item-wrapper">
      <h2>{{ editingBook ? 'Edit Book' : 'Add New Book' }}</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleSubmit"
      >
        <div class="add-item-form__item">
          <label for="isbn">ISBN:</label>
          <div style="display: flex; gap: var(--space-xs)">
            <input
              id="isbn"
              v-model="form.isbn"
              type="text"
              class="textbox"
              name="isbn"
            />
            <button
              type="button"
              class="button"
              :disabled="!form.isbn.trim()"
              @click="handleGoodreadsLookup"
            >
              <span class="button__text">Lookup</span>
            </button>
          </div>
        </div>
        <div class="add-item-form__item">
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
        <div class="add-item-form__item">
          <label for="author">Author:</label>
          <input
            id="author"
            v-model="form.author"
            type="text"
            class="textbox"
            name="author"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="tags">Tags (comma-separated):</label>
          <input
            id="tags"
            v-model="form.tags"
            type="text"
            class="textbox"
            name="tags"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="goodreads_url">Goodreads URL:</label>
          <input
            id="goodreads_url"
            v-model="form.goodreads_url"
            type="text"
            class="textbox"
            name="goodreads_url"
          />
        </div>
        <div class="add-item-form__item">
          <label for="priority">Priority:</label>
          <input
            id="priority"
            v-model="form.priority"
            type="number"
            class="textbox"
            name="priority"
          />
        </div>
        <div class="add-item-form__item">
          <label for="rating">Rating:</label>
          <input
            id="rating"
            v-model="form.rating"
            type="number"
            class="textbox"
            name="rating"
            min="1"
            max="5"
          />
        </div>
        <div class="add-item-form__item">
          <label for="purchase_date">Purchase Date:</label>
          <input
            id="purchase_date"
            v-model="form.purchase_date"
            type="date"
            class="textbox"
            name="purchase_date"
          />
        </div>
        <div class="add-item-form__item">
          <label for="purchase_price">Purchase Price:</label>
          <input
            id="purchase_price"
            v-model="form.purchase_price"
            type="number"
            class="textbox"
            name="purchase_price"
            step="0.01"
          />
        </div>
        <div class="add-item-form__item">
          <label for="sell_date">Sell Date:</label>
          <input
            id="sell_date"
            v-model="form.sell_date"
            type="date"
            class="textbox"
            name="sell_date"
          />
        </div>
        <div class="add-item-form__item">
          <label for="sell_price">Sell Price:</label>
          <input
            id="sell_price"
            v-model="form.sell_price"
            type="number"
            class="textbox"
            name="sell_price"
            step="0.01"
          />
        </div>
        <div class="add-item-form__item">
          <label for="read_start_date">Read Start Date:</label>
          <input
            id="read_start_date"
            v-model="form.read_start_date"
            type="date"
            class="textbox"
            name="read_start_date"
          />
        </div>
        <div class="add-item-form__item">
          <label for="read_finish_date">Read Finish Date:</label>
          <input
            id="read_finish_date"
            v-model="form.read_finish_date"
            type="date"
            class="textbox"
            name="read_finish_date"
          />
        </div>
        <div class="add-item-form__item">
          <label for="abandoned">
            <input
              id="abandoned"
              v-model="form.abandoned"
              type="checkbox"
              name="abandoned"
            />
            Abandoned
          </label>
        </div>
        <div class="add-item-form__item">
          <label for="location">Location:</label>
          <input
            id="location"
            v-model="form.location"
            type="text"
            class="textbox"
            name="location"
          />
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
        <div class="add-item-form__item add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">{{ editingBook ? 'Update Book' : 'Add Book' }}</span>
          </button>
          <button
            v-if="editingBook"
            type="button"
            class="button button--danger"
            @click="cancelEdit"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useBooksStore, deriveStatus } from '@/stores/books'
import type { BookStatus } from '@/stores/books'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Book } from '@/api/client'

const store = useBooksStore()
const { show: notify } = useNotifications()

const expandedBookId = ref<number | null>(null)
const editingBook = ref<Book | null>(null)
const searchInput = ref('')

const statusLabels: Record<BookStatus, string> = {
  sold: 'Sold',
  abandoned: 'Abandoned',
  read: 'Read',
  reading: 'Reading',
  'to-read': 'To Read',
}

const form = reactive({
  isbn: '',
  title: '',
  author: '',
  tags: '',
  goodreads_url: '',
  priority: '',
  rating: '',
  purchase_date: '',
  purchase_price: '',
  sell_date: '',
  sell_price: '',
  read_start_date: '',
  read_finish_date: '',
  abandoned: false,
  location: '',
  notes: '',
})

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

function resetForm() {
  form.isbn = ''
  form.title = ''
  form.author = ''
  form.tags = ''
  form.goodreads_url = ''
  form.priority = ''
  form.rating = ''
  form.purchase_date = ''
  form.purchase_price = ''
  form.sell_date = ''
  form.sell_price = ''
  form.read_start_date = ''
  form.read_finish_date = ''
  form.abandoned = false
  form.location = ''
  form.notes = ''
  editingBook.value = null
}

function startEdit(book: Book) {
  editingBook.value = book
  form.isbn = book.isbn ?? ''
  form.title = book.title
  form.author = book.author
  form.tags = book.tags.join(', ')
  form.goodreads_url = book.goodreads_url ?? ''
  form.priority = book.priority != null ? String(book.priority) : ''
  form.rating = book.rating != null ? String(book.rating) : ''
  form.purchase_date = book.purchase_date ? book.purchase_date.split('T')[0]! : ''
  form.purchase_price = book.purchase_price != null ? String(book.purchase_price) : ''
  form.sell_date = book.sell_date ? book.sell_date.split('T')[0]! : ''
  form.sell_price = book.sell_price != null ? String(book.sell_price) : ''
  form.read_start_date = book.read_start_date ? book.read_start_date.split('T')[0]! : ''
  form.read_finish_date = book.read_finish_date ? book.read_finish_date.split('T')[0]! : ''
  form.abandoned = book.abandoned ?? false
  form.location = book.location ?? ''
  form.notes = book.notes ?? ''
}

function cancelEdit() {
  resetForm()
}

function buildPayload() {
  const tags = form.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  return {
    isbn: form.isbn.trim() || undefined,
    title: form.title.trim(),
    author: form.author.trim(),
    tags,
    goodreads_url: form.goodreads_url.trim() || undefined,
    priority: form.priority ? Number(form.priority) : undefined,
    rating: form.rating ? Number(form.rating) : undefined,
    purchase_date: form.purchase_date || undefined,
    purchase_price: form.purchase_price ? Number(form.purchase_price) : undefined,
    sell_date: form.sell_date || undefined,
    sell_price: form.sell_price ? Number(form.sell_price) : undefined,
    read_start_date: form.read_start_date || undefined,
    read_finish_date: form.read_finish_date || undefined,
    abandoned: form.abandoned || undefined,
    location: form.location.trim() || undefined,
    notes: form.notes.trim() || undefined,
  }
}

async function handleSubmit() {
  if (!form.title.trim() || !form.author.trim() || !form.tags.trim()) return

  try {
    if (editingBook.value) {
      await store.update(editingBook.value.id, buildPayload())
      notify('Book updated', 'success')
    } else {
      await store.create(buildPayload() as Parameters<typeof store.create>[0])
      notify('Book added', 'success')
    }
    resetForm()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    const action = editingBook.value ? 'update' : 'add'
    notify(`Failed to ${action} book: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    if (editingBook.value?.id === id) {
      resetForm()
    }
    notify('Book deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete book: ${detail}`, 'error')
  }
}

async function handleGoodreadsLookup() {
  if (!form.isbn.trim()) return
  try {
    const info = await store.fetchGoodreadsInfo(form.isbn.trim())
    form.title = info.title
    form.author = info.author
    form.tags = info.tags
    form.goodreads_url = info.goodreads_url
    notify('Goodreads info loaded', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Goodreads lookup failed: ${detail}`, 'error')
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
</style>
