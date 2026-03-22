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
        <h2>{{ editData ? 'Edit Countdown' : 'Add Countdown' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="countdown-name">Name</label>
          <input
            id="countdown-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="countdown-name-input"
            type="text"
            size="30"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="countdown-due-date">Due Date</label>
          <DatePicker
            id="countdown-due-date"
            data-testid="countdown-due-date-input"
            :model-value="form.due_date"
            required
            @update:model-value="form.due_date = $event"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="countdown-notes">Notes</label>
          <textarea
            id="countdown-notes"
            v-model="form.notes"
            data-testid="countdown-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="countdown-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Countdown</span>
          </button>
          <button
            type="button"
            data-testid="countdown-cancel-button"
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
import type { CountdownCreate, CountdownUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'

const props = defineProps<{
  visible: boolean
  editData?: { id: number; name: string; due_date: string; notes?: string } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: CountdownCreate]
  update: [id: number, data: CountdownUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  due_date: '',
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.due_date = props.editData.due_date
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.due_date = ''
  form.notes = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.due_date) return
  if (props.editData) {
    emit('update', props.editData.id, {
      name: form.name.trim(),
      due_date: form.due_date,
      notes: form.notes.trim() || undefined,
    })
  } else {
    emit('create', {
      name: form.name.trim(),
      due_date: form.due_date,
      notes: form.notes.trim() || undefined,
    })
  }
  handleSuccess()
}
</script>
