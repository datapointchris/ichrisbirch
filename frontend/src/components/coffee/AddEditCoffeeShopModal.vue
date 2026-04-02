<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="nameInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Coffee Shop' : 'Add Coffee Shop' }}</h2>

        <!-- name -->
        <div class="add-edit-modal__form-item">
          <label for="shop-name">Name</label>
          <input
            id="shop-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="shop-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <!-- address -->
        <div class="add-edit-modal__form-item">
          <label for="shop-address">Address</label>
          <input
            id="shop-address"
            v-model="form.address"
            data-testid="shop-address-input"
            type="text"
            class="textbox"
          />
        </div>

        <!-- city, state -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="shop-city">City</label>
            <input
              id="shop-city"
              v-model="form.city"
              data-testid="shop-city-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="shop-state">State</label>
            <input
              id="shop-state"
              v-model="form.state"
              data-testid="shop-state-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- country, google maps url -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="shop-country">Country</label>
            <input
              id="shop-country"
              v-model="form.country"
              data-testid="shop-country-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="shop-google-maps-url">Google Maps URL</label>
            <input
              id="shop-google-maps-url"
              v-model="form.google_maps_url"
              data-testid="shop-google-maps-url-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- website, rating -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="shop-website">Website</label>
            <input
              id="shop-website"
              v-model="form.website"
              data-testid="shop-website-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="shop-rating">Rating (1-5)</label>
            <input
              id="shop-rating"
              v-model="form.rating"
              data-testid="shop-rating-input"
              type="number"
              min="1"
              max="5"
              step="0.1"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- date visited -->
        <div class="add-edit-modal__form-item">
          <label for="shop-date-visited">Date Visited</label>
          <DatePicker
            id="shop-date-visited"
            data-testid="shop-date-visited-input"
            :model-value="form.date_visited"
            @update:model-value="form.date_visited = $event"
          />
        </div>

        <!-- notes -->
        <div class="add-edit-modal__form-item">
          <label for="shop-notes">Notes</label>
          <textarea
            id="shop-notes"
            v-model="form.notes"
            data-testid="shop-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <!-- review -->
        <div class="add-edit-modal__form-item">
          <label for="shop-review">Review</label>
          <textarea
            id="shop-review"
            v-model="form.review"
            data-testid="shop-review-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="shop-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Shop</span>
          </button>
          <button
            type="button"
            data-testid="shop-cancel-button"
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
import type { CoffeeShop, CoffeeShopCreate, CoffeeShopUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'

const props = defineProps<{
  visible: boolean
  editData?: CoffeeShop | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: CoffeeShopCreate]
  update: [id: number, data: CoffeeShopUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

function createEmptyForm() {
  return {
    name: '',
    address: '',
    city: '',
    state: '',
    country: '',
    google_maps_url: '',
    website: '',
    rating: '',
    date_visited: '',
    notes: '',
    review: '',
  }
}

const form = reactive(createEmptyForm())

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const shop = props.editData
      form.name = shop.name
      form.address = shop.address ?? ''
      form.city = shop.city ?? ''
      form.state = shop.state ?? ''
      form.country = shop.country ?? ''
      form.google_maps_url = shop.google_maps_url ?? ''
      form.website = shop.website ?? ''
      form.rating = shop.rating != null ? String(shop.rating) : ''
      form.date_visited = shop.date_visited ? shop.date_visited.split('T')[0]! : ''
      form.notes = shop.notes ?? ''
      form.review = shop.review ?? ''
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
  const emptyVal = props.editData ? null : undefined
  return {
    name: form.name.trim(),
    address: form.address.trim() || emptyVal,
    city: form.city.trim() || emptyVal,
    state: form.state.trim() || emptyVal,
    country: form.country.trim() || emptyVal,
    google_maps_url: form.google_maps_url.trim() || emptyVal,
    website: form.website.trim() || emptyVal,
    rating: form.rating ? Number(form.rating) : emptyVal,
    date_visited: form.date_visited || emptyVal,
    notes: form.notes.trim() || emptyVal,
    review: form.review.trim() || emptyVal,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, buildPayload() as CoffeeShopUpdate)
  } else {
    emit('create', buildPayload() as CoffeeShopCreate)
  }
  handleSuccess()
}
</script>
