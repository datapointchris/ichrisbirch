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

            <!-- Inline Edit Form -->
            <div
              v-if="editingBookId === book.id"
              class="books__edit books__edit--open"
            >
              <h3>Edit Book</h3>
              <form
                class="add-item-form"
                @submit.prevent="handleEditSubmit"
              >
                <div class="add-item-form__item">
                  <label :for="`edit-isbn-${book.id}`">ISBN:</label>
                  <div style="display: flex; gap: var(--space-xs)">
                    <input
                      :id="`edit-isbn-${book.id}`"
                      v-model="editForm.isbn"
                      type="text"
                      class="textbox"
                    />
                    <button
                      type="button"
                      class="button"
                      :disabled="!editForm.isbn.trim()"
                      @click="handleEditGoodreadsLookup"
                    >
                      <span class="button__text">Lookup</span>
                    </button>
                  </div>
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-title-${book.id}`">Title:</label>
                  <input
                    :id="`edit-title-${book.id}`"
                    v-model="editForm.title"
                    type="text"
                    class="textbox"
                    required
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-author-${book.id}`">Author:</label>
                  <input
                    :id="`edit-author-${book.id}`"
                    v-model="editForm.author"
                    type="text"
                    class="textbox"
                    required
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-tags-${book.id}`">Tags (comma-separated):</label>
                  <input
                    :id="`edit-tags-${book.id}`"
                    v-model="editForm.tags"
                    type="text"
                    class="textbox"
                    required
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-goodreads_url-${book.id}`">Goodreads URL:</label>
                  <input
                    :id="`edit-goodreads_url-${book.id}`"
                    v-model="editForm.goodreads_url"
                    type="text"
                    class="textbox"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-priority-${book.id}`">Priority:</label>
                  <input
                    :id="`edit-priority-${book.id}`"
                    v-model="editForm.priority"
                    type="number"
                    class="textbox"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-rating-${book.id}`">Rating:</label>
                  <input
                    :id="`edit-rating-${book.id}`"
                    v-model="editForm.rating"
                    type="number"
                    class="textbox"
                    min="1"
                    max="5"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-purchase_date-${book.id}`">Purchase Date:</label>
                  <DatePicker
                    :model-value="editForm.purchase_date"
                    @update:model-value="editForm.purchase_date = $event"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-purchase_price-${book.id}`">Purchase Price:</label>
                  <input
                    :id="`edit-purchase_price-${book.id}`"
                    v-model="editForm.purchase_price"
                    type="number"
                    class="textbox"
                    step="0.01"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-sell_date-${book.id}`">Sell Date:</label>
                  <DatePicker
                    :model-value="editForm.sell_date"
                    @update:model-value="editForm.sell_date = $event"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-sell_price-${book.id}`">Sell Price:</label>
                  <input
                    :id="`edit-sell_price-${book.id}`"
                    v-model="editForm.sell_price"
                    type="number"
                    class="textbox"
                    step="0.01"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-read_start_date-${book.id}`">Read Start Date:</label>
                  <DatePicker
                    :model-value="editForm.read_start_date"
                    @update:model-value="editForm.read_start_date = $event"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-read_finish_date-${book.id}`">Read Finish Date:</label>
                  <DatePicker
                    :model-value="editForm.read_finish_date"
                    @update:model-value="editForm.read_finish_date = $event"
                  />
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-progress-${book.id}`">Progress:</label>
                  <select
                    :id="`edit-progress-${book.id}`"
                    v-model="editForm.progress"
                    class="textbox"
                  >
                    <option
                      v-for="(label, value) in statusLabels"
                      :key="value"
                      :value="value"
                    >
                      {{ label }}
                    </option>
                  </select>
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-ownership-${book.id}`">Ownership:</label>
                  <select
                    :id="`edit-ownership-${book.id}`"
                    v-model="editForm.ownership"
                    class="textbox"
                  >
                    <option
                      v-for="(label, value) in ownershipLabels"
                      :key="value"
                      :value="value"
                    >
                      {{ label }}
                    </option>
                  </select>
                </div>
                <div class="add-item-form__item">
                  <label :for="`edit-location-${book.id}`">Location:</label>
                  <input
                    :id="`edit-location-${book.id}`"
                    v-model="editForm.location"
                    type="text"
                    class="textbox"
                  />
                </div>
                <div class="add-item-form__item add-item-form__item--full-width">
                  <label :for="`edit-notes-${book.id}`">Notes:</label>
                  <textarea
                    :id="`edit-notes-${book.id}`"
                    v-model="editForm.notes"
                    rows="3"
                    class="textbox"
                  ></textarea>
                </div>
                <div class="add-item-form__item add-item-form__item--full-width">
                  <label :for="`edit-review-${book.id}`">Review:</label>
                  <textarea
                    :id="`edit-review-${book.id}`"
                    v-model="editForm.review"
                    rows="3"
                    class="textbox"
                  ></textarea>
                </div>
                <div class="add-item-form__item add-item-form__item--full-width">
                  <button
                    type="submit"
                    class="button"
                  >
                    <span class="button__text">Update Book</span>
                  </button>
                  <button
                    type="button"
                    class="button button--danger"
                    @click="cancelEdit"
                  >
                    <span class="button__text button__text--danger">Cancel</span>
                  </button>
                </div>
              </form>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Add New Book Form -->
    <div class="add-item-wrapper">
      <h2>Add New Book</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleAddSubmit"
      >
        <div class="add-item-form__item">
          <label for="isbn">ISBN:</label>
          <div style="display: flex; gap: var(--space-xs)">
            <input
              id="isbn"
              v-model="addForm.isbn"
              type="text"
              class="textbox"
              name="isbn"
            />
            <button
              type="button"
              class="button"
              :disabled="!addForm.isbn.trim()"
              @click="handleAddGoodreadsLookup"
            >
              <span class="button__text">Lookup</span>
            </button>
          </div>
        </div>
        <div class="add-item-form__item">
          <label for="title">Title:</label>
          <input
            id="title"
            v-model="addForm.title"
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
            v-model="addForm.author"
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
            v-model="addForm.tags"
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
            v-model="addForm.goodreads_url"
            type="text"
            class="textbox"
            name="goodreads_url"
          />
        </div>
        <div class="add-item-form__item">
          <label for="priority">Priority:</label>
          <input
            id="priority"
            v-model="addForm.priority"
            type="number"
            class="textbox"
            name="priority"
          />
        </div>
        <div class="add-item-form__item">
          <label for="rating">Rating:</label>
          <input
            id="rating"
            v-model="addForm.rating"
            type="number"
            class="textbox"
            name="rating"
            min="1"
            max="5"
          />
        </div>
        <div class="add-item-form__item">
          <label for="purchase_date">Purchase Date:</label>
          <DatePicker
            :model-value="addForm.purchase_date"
            @update:model-value="addForm.purchase_date = $event"
          />
        </div>
        <div class="add-item-form__item">
          <label for="purchase_price">Purchase Price:</label>
          <input
            id="purchase_price"
            v-model="addForm.purchase_price"
            type="number"
            class="textbox"
            name="purchase_price"
            step="0.01"
          />
        </div>
        <div class="add-item-form__item">
          <label for="sell_date">Sell Date:</label>
          <DatePicker
            :model-value="addForm.sell_date"
            @update:model-value="addForm.sell_date = $event"
          />
        </div>
        <div class="add-item-form__item">
          <label for="sell_price">Sell Price:</label>
          <input
            id="sell_price"
            v-model="addForm.sell_price"
            type="number"
            class="textbox"
            name="sell_price"
            step="0.01"
          />
        </div>
        <div class="add-item-form__item">
          <label for="read_start_date">Read Start Date:</label>
          <DatePicker
            :model-value="addForm.read_start_date"
            @update:model-value="addForm.read_start_date = $event"
          />
        </div>
        <div class="add-item-form__item">
          <label for="read_finish_date">Read Finish Date:</label>
          <DatePicker
            :model-value="addForm.read_finish_date"
            @update:model-value="addForm.read_finish_date = $event"
          />
        </div>
        <div class="add-item-form__item">
          <label for="progress">Progress:</label>
          <select
            id="progress"
            v-model="addForm.progress"
            class="textbox"
            name="progress"
          >
            <option
              v-for="(label, value) in statusLabels"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </div>
        <div class="add-item-form__item">
          <label for="ownership">Ownership:</label>
          <select
            id="ownership"
            v-model="addForm.ownership"
            class="textbox"
            name="ownership"
          >
            <option
              v-for="(label, value) in ownershipLabels"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </div>
        <div class="add-item-form__item">
          <label for="location">Location:</label>
          <input
            id="location"
            v-model="addForm.location"
            type="text"
            class="textbox"
            name="location"
          />
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="notes">Notes:</label>
          <textarea
            id="notes"
            v-model="addForm.notes"
            rows="3"
            class="textbox"
            name="notes"
          ></textarea>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="review">Review:</label>
          <textarea
            id="review"
            v-model="addForm.review"
            rows="3"
            class="textbox"
            name="review"
          ></textarea>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Book</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useBooksStore } from '@/stores/books'
import type { BookProgress, BookOwnership } from '@/stores/books'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Book } from '@/api/client'
import DatePicker from '@/components/DatePicker.vue'

const store = useBooksStore()
const { show: notify } = useNotifications()

const expandedBookId = ref<number | null>(null)
const editingBookId = ref<number | null>(null)
const searchInput = ref('')

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

function createEmptyForm() {
  return {
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
    progress: 'unread' as BookProgress,
    ownership: 'owned' as BookOwnership,
    location: '',
    notes: '',
    review: '',
  }
}

const addForm = reactive(createEmptyForm())
const editForm = reactive(createEmptyForm())

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

function resetAddForm() {
  Object.assign(addForm, createEmptyForm())
}

function startEdit(book: Book) {
  editingBookId.value = book.id
  expandedBookId.value = null
  editForm.isbn = book.isbn ?? ''
  editForm.title = book.title
  editForm.author = book.author
  editForm.tags = book.tags.join(', ')
  editForm.goodreads_url = book.goodreads_url ?? ''
  editForm.priority = book.priority != null ? String(book.priority) : ''
  editForm.rating = book.rating != null ? String(book.rating) : ''
  editForm.purchase_date = book.purchase_date ? book.purchase_date.split('T')[0]! : ''
  editForm.purchase_price = book.purchase_price != null ? String(book.purchase_price) : ''
  editForm.sell_date = book.sell_date ? book.sell_date.split('T')[0]! : ''
  editForm.sell_price = book.sell_price != null ? String(book.sell_price) : ''
  editForm.read_start_date = book.read_start_date ? book.read_start_date.split('T')[0]! : ''
  editForm.read_finish_date = book.read_finish_date ? book.read_finish_date.split('T')[0]! : ''
  editForm.progress = (book.progress ?? 'unread') as BookProgress
  editForm.ownership = (book.ownership ?? 'owned') as BookOwnership
  editForm.location = book.location ?? ''
  editForm.notes = book.notes ?? ''
  editForm.review = book.review ?? ''
}

function cancelEdit() {
  editingBookId.value = null
  Object.assign(editForm, createEmptyForm())
}

function buildAddPayload() {
  const tags = addForm.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  return {
    isbn: addForm.isbn.trim() || undefined,
    title: addForm.title.trim(),
    author: addForm.author.trim(),
    tags,
    goodreads_url: addForm.goodreads_url.trim() || undefined,
    priority: addForm.priority ? Number(addForm.priority) : undefined,
    rating: addForm.rating ? Number(addForm.rating) : undefined,
    purchase_date: addForm.purchase_date || undefined,
    purchase_price: addForm.purchase_price ? Number(addForm.purchase_price) : undefined,
    sell_date: addForm.sell_date || undefined,
    sell_price: addForm.sell_price ? Number(addForm.sell_price) : undefined,
    read_start_date: addForm.read_start_date || undefined,
    read_finish_date: addForm.read_finish_date || undefined,
    progress: addForm.progress,
    ownership: addForm.ownership,
    location: addForm.location.trim() || undefined,
    notes: addForm.notes.trim() || undefined,
    review: addForm.review.trim() || undefined,
  }
}

// For edits, empty fields send null (to clear the value) instead of undefined (which omits the field)
function buildEditPayload() {
  const tags = editForm.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  return {
    isbn: editForm.isbn.trim() || null,
    title: editForm.title.trim(),
    author: editForm.author.trim(),
    tags,
    goodreads_url: editForm.goodreads_url.trim() || null,
    priority: editForm.priority ? Number(editForm.priority) : null,
    rating: editForm.rating ? Number(editForm.rating) : null,
    purchase_date: editForm.purchase_date || null,
    purchase_price: editForm.purchase_price ? Number(editForm.purchase_price) : null,
    sell_date: editForm.sell_date || null,
    sell_price: editForm.sell_price ? Number(editForm.sell_price) : null,
    read_start_date: editForm.read_start_date || null,
    read_finish_date: editForm.read_finish_date || null,
    progress: editForm.progress,
    ownership: editForm.ownership,
    location: editForm.location.trim() || null,
    notes: editForm.notes.trim() || null,
    review: editForm.review.trim() || null,
  }
}

async function handleEditSubmit() {
  if (!editForm.title.trim() || !editForm.author.trim() || !editForm.tags.trim()) return
  if (!editingBookId.value) return

  try {
    await store.update(editingBookId.value, buildEditPayload())
    notify(`${editForm.title.trim()}: ${editForm.author.trim()} | updated`, 'success')
    cancelEdit()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`${editForm.title.trim()}: ${editForm.author.trim()} | update failed: ${detail}`, 'error')
  }
}

async function handleAddSubmit() {
  if (!addForm.title.trim() || !addForm.author.trim() || !addForm.tags.trim()) return

  try {
    await store.create(buildAddPayload() as Parameters<typeof store.create>[0])
    notify(`${addForm.title.trim()}: ${addForm.author.trim()} | added`, 'success')
    resetAddForm()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`${addForm.title.trim()}: ${addForm.author.trim()} | add failed: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  const book = store.books.find((b) => b.id === id)
  const label = book ? `${book.title}: ${book.author}` : `Book ${id}`
  try {
    await store.remove(id)
    if (editingBookId.value === id) {
      cancelEdit()
    }
    notify(`${label} | deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`${label} | delete failed: ${detail}`, 'error')
  }
}

async function handleAddGoodreadsLookup() {
  if (!addForm.isbn.trim()) return
  try {
    const info = await store.fetchGoodreadsInfo(addForm.isbn.trim())
    addForm.title = info.title
    addForm.author = info.author
    addForm.tags = info.tags
    addForm.goodreads_url = info.goodreads_url
    notify('Goodreads info loaded', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Goodreads lookup failed: ${detail}`, 'error')
  }
}

async function handleEditGoodreadsLookup() {
  if (!editForm.isbn.trim()) return
  try {
    const info = await store.fetchGoodreadsInfo(editForm.isbn.trim())
    editForm.title = info.title
    editForm.author = info.author
    editForm.tags = info.tags
    editForm.goodreads_url = info.goodreads_url
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

.books__filter-select {
  width: auto;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-300);
}
</style>
