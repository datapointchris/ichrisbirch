<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="titleInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Book' : 'Add Book' }}</h2>

        <!-- isbn, lookup button -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-isbn">ISBN</label>
            <input
              id="book-isbn"
              v-model="form.isbn"
              data-testid="book-isbn-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label>&nbsp;</label>
            <button
              type="button"
              data-testid="book-goodreads-button"
              class="button"
              :disabled="!form.isbn.trim()"
              @click="handleGoodreadsLookup"
            >
              <span class="button__text">Lookup</span>
            </button>
          </div>
        </div>

        <!-- title -->
        <div class="add-edit-modal__form-item">
          <label for="book-title">Title</label>
          <input
            id="book-title"
            ref="titleInput"
            v-model="form.title"
            data-testid="book-title-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <!-- author, tags -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-author">Author</label>
            <input
              id="book-author"
              v-model="form.author"
              data-testid="book-author-input"
              type="text"
              class="textbox"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="book-tags">Tags (comma-separated)</label>
            <input
              id="book-tags"
              v-model="form.tags"
              data-testid="book-tags-input"
              type="text"
              class="textbox"
              required
            />
          </div>
        </div>

        <!-- goodreads url -->
        <div class="add-edit-modal__form-item">
          <label for="book-goodreads-url">Goodreads URL</label>
          <input
            id="book-goodreads-url"
            v-model="form.goodreads_url"
            data-testid="book-goodreads-url-input"
            type="text"
            class="textbox"
          />
        </div>

        <!-- priority, rating -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-priority">Priority</label>
            <input
              id="book-priority"
              v-model="form.priority"
              data-testid="book-priority-input"
              type="number"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="book-rating">Rating</label>
            <input
              id="book-rating"
              v-model="form.rating"
              data-testid="book-rating-input"
              type="number"
              min="1"
              max="5"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- purchase date, purchase price -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-purchase-date">Purchase Date</label>
            <DatePicker
              id="book-purchase-date"
              data-testid="book-purchase-date-input"
              :model-value="form.purchase_date"
              @update:model-value="form.purchase_date = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="book-purchase-price">Purchase Price</label>
            <input
              id="book-purchase-price"
              v-model="form.purchase_price"
              data-testid="book-purchase-price-input"
              type="number"
              step="0.01"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- sell date, sell price -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-sell-date">Sell Date</label>
            <DatePicker
              id="book-sell-date"
              data-testid="book-sell-date-input"
              :model-value="form.sell_date"
              @update:model-value="form.sell_date = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="book-sell-price">Sell Price</label>
            <input
              id="book-sell-price"
              v-model="form.sell_price"
              data-testid="book-sell-price-input"
              type="number"
              step="0.01"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- read start date, read finish date -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-read-start">Read Start Date</label>
            <DatePicker
              id="book-read-start"
              data-testid="book-read-start-input"
              :model-value="form.read_start_date"
              @update:model-value="form.read_start_date = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="book-read-finish">Read Finish Date</label>
            <DatePicker
              id="book-read-finish"
              data-testid="book-read-finish-input"
              :model-value="form.read_finish_date"
              @update:model-value="form.read_finish_date = $event"
            />
          </div>
        </div>

        <!-- progress, ownership, location -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="book-progress">Progress</label>
            <select
              id="book-progress"
              v-model="form.progress"
              data-testid="book-progress-input"
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
          <div class="add-edit-modal__form-item">
            <label for="book-ownership">Ownership</label>
            <select
              id="book-ownership"
              v-model="form.ownership"
              data-testid="book-ownership-input"
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
          <div class="add-edit-modal__form-item">
            <label for="book-location">Location</label>
            <input
              id="book-location"
              v-model="form.location"
              data-testid="book-location-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="book-notes">Notes</label>
          <textarea
            id="book-notes"
            v-model="form.notes"
            data-testid="book-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="book-review">Review</label>
          <textarea
            id="book-review"
            v-model="form.review"
            data-testid="book-review-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="book-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Book</span>
          </button>
          <button
            type="button"
            data-testid="book-cancel-button"
            class="button button--danger"
            @click="handleClose()"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { Book, BookCreate, BookUpdate } from '@/api/client'
import type { BookProgress, BookOwnership } from '@/stores/books'
import { useBooksStore } from '@/stores/books'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'

const props = defineProps<{
  visible: boolean
  editData?: Book | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: BookCreate]
  update: [id: number, data: BookUpdate]
}>()

const store = useBooksStore()
const { show: notify } = useNotifications()

const titleInput = ref<HTMLInputElement | null>(null)

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

const form = reactive(createEmptyForm())

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const book = props.editData
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
      form.progress = (book.progress ?? 'unread') as BookProgress
      form.ownership = (book.ownership ?? 'owned') as BookOwnership
      form.location = book.location ?? ''
      form.notes = book.notes ?? ''
      form.review = book.review ?? ''
    }
  }
)

function resetForm() {
  Object.assign(form, createEmptyForm())
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function buildPayload() {
  const tags = form.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  const emptyVal = props.editData ? null : undefined
  return {
    isbn: form.isbn.trim() || emptyVal,
    title: form.title.trim(),
    author: form.author.trim(),
    tags,
    goodreads_url: form.goodreads_url.trim() || emptyVal,
    priority: form.priority ? Number(form.priority) : emptyVal,
    rating: form.rating ? Number(form.rating) : emptyVal,
    purchase_date: form.purchase_date || emptyVal,
    purchase_price: form.purchase_price ? Number(form.purchase_price) : emptyVal,
    sell_date: form.sell_date || emptyVal,
    sell_price: form.sell_price ? Number(form.sell_price) : emptyVal,
    read_start_date: form.read_start_date || emptyVal,
    read_finish_date: form.read_finish_date || emptyVal,
    progress: form.progress,
    ownership: form.ownership,
    location: form.location.trim() || emptyVal,
    notes: form.notes.trim() || emptyVal,
    review: form.review.trim() || emptyVal,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.title.trim() || !form.author.trim() || !form.tags.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, buildPayload() as BookUpdate)
  } else {
    emit('create', buildPayload() as BookCreate)
  }
  handleSuccess()
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
</script>
