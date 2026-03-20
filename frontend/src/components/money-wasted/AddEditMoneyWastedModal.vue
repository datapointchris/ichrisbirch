<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="itemInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Entry' : 'Add Money Wasted' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="mw-item">Item</label>
          <input
            id="mw-item"
            ref="itemInput"
            v-model="form.item"
            data-testid="mw-item-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="mw-date-purchased">Date Purchased</label>
          <DatePicker
            id="mw-date-purchased"
            data-testid="mw-date-purchased-input"
            :model-value="form.date_purchased"
            @update:model-value="form.date_purchased = $event"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="mw-amount">Amount</label>
          <input
            id="mw-amount"
            v-model="form.amount"
            data-testid="mw-amount-input"
            type="number"
            step="0.01"
            min="0"
            class="textbox add-edit-modal__number-input"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="mw-date-wasted">Date Wasted</label>
          <DatePicker
            id="mw-date-wasted"
            data-testid="mw-date-wasted-input"
            :model-value="form.date_wasted"
            required
            @update:model-value="form.date_wasted = $event"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="mw-notes">Notes</label>
          <textarea
            id="mw-notes"
            v-model="form.notes"
            data-testid="mw-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="mw-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Entry</span>
          </button>
          <button
            type="button"
            data-testid="mw-cancel-button"
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
import type { MoneyWasted, MoneyWastedCreate, MoneyWastedUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'

const props = defineProps<{
  visible: boolean
  editData?: MoneyWasted | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: MoneyWastedCreate]
  update: [id: number, data: MoneyWastedUpdate]
}>()

const itemInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  item: '',
  amount: '',
  date_purchased: '',
  date_wasted: '',
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.item = props.editData.item
      form.amount = String(props.editData.amount)
      form.date_purchased = props.editData.date_purchased ?? ''
      form.date_wasted = props.editData.date_wasted
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.item = ''
  form.amount = ''
  form.date_purchased = ''
  form.date_wasted = ''
  form.notes = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.item.trim() || !form.date_wasted) return
  const data = {
    item: form.item.trim(),
    amount: Number(form.amount),
    date_purchased: form.date_purchased || undefined,
    date_wasted: form.date_wasted,
    notes: form.notes.trim() || undefined,
  }
  if (props.editData) {
    emit('update', props.editData.id, data)
  } else {
    emit('create', data)
  }
  handleSuccess()
}
</script>
