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
        <h2>{{ editData ? 'Edit Coffee Bean' : 'Add Coffee Bean' }}</h2>

        <!-- name, roaster -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-name">Name</label>
            <input
              id="bean-name"
              ref="nameInput"
              v-model="form.name"
              data-testid="bean-name-input"
              type="text"
              class="textbox"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="bean-roaster">Roaster</label>
            <input
              id="bean-roaster"
              v-model="form.roaster"
              data-testid="bean-roaster-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- origin, process -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-origin">Origin</label>
            <input
              id="bean-origin"
              v-model="form.origin"
              data-testid="bean-origin-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="bean-process">Process</label>
            <NeuSelect
              :model-value="form.process"
              :options="processOptions"
              data-testid="bean-process-input"
              @update:model-value="form.process = $event"
            />
          </div>
        </div>

        <!-- roast level, brew method -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-roast-level">Roast Level</label>
            <NeuSelect
              :model-value="form.roast_level"
              :options="roastLevelOptions"
              data-testid="bean-roast-level-input"
              @update:model-value="form.roast_level = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="bean-brew-method">Brew Method</label>
            <NeuSelect
              :model-value="form.brew_method"
              :options="brewMethodOptions"
              data-testid="bean-brew-method-input"
              @update:model-value="form.brew_method = $event"
            />
          </div>
        </div>

        <!-- rating, price -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-rating">Rating (1-5)</label>
            <input
              id="bean-rating"
              v-model="form.rating"
              data-testid="bean-rating-input"
              type="number"
              min="1"
              max="5"
              step="0.1"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="bean-price">Price ($)</label>
            <input
              id="bean-price"
              v-model="form.price"
              data-testid="bean-price-input"
              type="number"
              min="0"
              step="0.01"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- purchase date, purchase url -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-purchase-date">Purchase Date</label>
            <DatePicker
              id="bean-purchase-date"
              data-testid="bean-purchase-date-input"
              :model-value="form.purchase_date"
              @update:model-value="form.purchase_date = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="bean-purchase-url">Purchase URL</label>
            <input
              id="bean-purchase-url"
              v-model="form.purchase_url"
              data-testid="bean-purchase-url-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- purchase source: shop or other -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="bean-coffee-shop">Purchased From (Shop)</label>
            <NeuSelect
              :model-value="form.coffee_shop_id_str"
              :options="shopOptions"
              data-testid="bean-coffee-shop-input"
              @update:model-value="handleShopSelect($event)"
            />
          </div>
          <div
            v-if="form.coffee_shop_id_str === 'other'"
            class="add-edit-modal__form-item"
          >
            <label for="bean-purchase-source">Other Source</label>
            <input
              id="bean-purchase-source"
              v-model="form.purchase_source"
              data-testid="bean-purchase-source-input"
              type="text"
              class="textbox"
              placeholder="e.g. Trade Coffee subscription"
            />
          </div>
        </div>

        <!-- flavor notes -->
        <div class="add-edit-modal__form-item">
          <label for="bean-flavor-notes">Flavor Notes (comma-separated)</label>
          <textarea
            id="bean-flavor-notes"
            v-model="form.flavor_notes"
            data-testid="bean-flavor-notes-input"
            rows="2"
            class="textbox"
            placeholder="e.g. chocolate, citrus, honey"
          ></textarea>
        </div>

        <!-- notes -->
        <div class="add-edit-modal__form-item">
          <label for="bean-notes">Notes</label>
          <textarea
            id="bean-notes"
            v-model="form.notes"
            data-testid="bean-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <!-- review -->
        <div class="add-edit-modal__form-item">
          <label for="bean-review">Review</label>
          <textarea
            id="bean-review"
            v-model="form.review"
            data-testid="bean-review-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="bean-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Bean</span>
          </button>
          <button
            type="button"
            data-testid="bean-cancel-button"
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
import { reactive, ref, watch, computed } from 'vue'
import type { CoffeeBean, CoffeeBeanCreate, CoffeeBeanUpdate } from '@/api/client'
import { ROAST_LEVELS, BREW_METHODS } from '@/stores/coffeeBeans'
import { useCoffeeShopsStore } from '@/stores/coffeeShops'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const props = defineProps<{
  visible: boolean
  editData?: CoffeeBean | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: CoffeeBeanCreate]
  update: [id: number, data: CoffeeBeanUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)
const shopsStore = useCoffeeShopsStore()

const processOptions = [
  { value: '', label: '— none —' },
  { value: 'washed', label: 'Washed' },
  { value: 'natural', label: 'Natural' },
  { value: 'honey', label: 'Honey' },
  { value: 'anaerobic', label: 'Anaerobic' },
]

const roastLevelOptions = [
  { value: '', label: '— none —' },
  ...ROAST_LEVELS.map((r) => ({ value: r, label: r.charAt(0).toUpperCase() + r.slice(1) })),
]

const brewMethodOptions = [
  { value: '', label: '— none —' },
  ...BREW_METHODS.map((m) => ({ value: m, label: m.charAt(0).toUpperCase() + m.slice(1) })),
]

const shopOptions = computed(() => [
  { value: '', label: '— none —' },
  ...shopsStore.items.map((s) => ({ value: String(s.id), label: s.name })),
  { value: 'other', label: 'Other source…' },
])

function createEmptyForm() {
  return {
    name: '',
    roaster: '',
    origin: '',
    process: '',
    roast_level: '',
    brew_method: '',
    flavor_notes: '',
    rating: '',
    review: '',
    notes: '',
    price: '',
    purchase_date: '',
    coffee_shop_id_str: '', // 'other' | '' | '<id>'
    purchase_source: '',
    purchase_url: '',
  }
}

const form = reactive(createEmptyForm())

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const bean = props.editData
      form.name = bean.name
      form.roaster = bean.roaster ?? ''
      form.origin = bean.origin ?? ''
      form.process = bean.process ?? ''
      form.roast_level = bean.roast_level ?? ''
      form.brew_method = bean.brew_method ?? ''
      form.flavor_notes = bean.flavor_notes ?? ''
      form.rating = bean.rating != null ? String(bean.rating) : ''
      form.review = bean.review ?? ''
      form.notes = bean.notes ?? ''
      form.price = bean.price != null ? String(bean.price) : ''
      form.purchase_date = bean.purchase_date ? bean.purchase_date.split('T')[0]! : ''
      form.purchase_url = bean.purchase_url ?? ''
      if (bean.coffee_shop_id != null) {
        form.coffee_shop_id_str = String(bean.coffee_shop_id)
        form.purchase_source = ''
      } else if (bean.purchase_source) {
        form.coffee_shop_id_str = 'other'
        form.purchase_source = bean.purchase_source
      } else {
        form.coffee_shop_id_str = ''
        form.purchase_source = ''
      }
    }
  }
)

function handleShopSelect(value: string) {
  form.coffee_shop_id_str = value
  if (value !== 'other') {
    form.purchase_source = ''
  }
}

function resetForm() {
  Object.assign(form, createEmptyForm())
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function buildPayload() {
  const emptyVal = props.editData ? null : undefined
  const coffeeShopId = form.coffee_shop_id_str && form.coffee_shop_id_str !== 'other' ? Number(form.coffee_shop_id_str) : emptyVal
  const purchaseSource = form.coffee_shop_id_str === 'other' ? form.purchase_source.trim() || emptyVal : emptyVal
  return {
    name: form.name.trim(),
    roaster: form.roaster.trim() || emptyVal,
    origin: form.origin.trim() || emptyVal,
    process: form.process || emptyVal,
    roast_level: form.roast_level || emptyVal,
    brew_method: form.brew_method || emptyVal,
    flavor_notes: form.flavor_notes.trim() || emptyVal,
    rating: form.rating ? Number(form.rating) : emptyVal,
    review: form.review.trim() || emptyVal,
    notes: form.notes.trim() || emptyVal,
    price: form.price ? Number(form.price) : emptyVal,
    purchase_date: form.purchase_date || emptyVal,
    coffee_shop_id: coffeeShopId,
    purchase_source: purchaseSource,
    purchase_url: form.purchase_url.trim() || emptyVal,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, buildPayload() as CoffeeBeanUpdate)
  } else {
    emit('create', buildPayload() as CoffeeBeanCreate)
  }
  handleSuccess()
}
</script>
