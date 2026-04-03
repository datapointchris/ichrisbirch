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
        <h2>{{ editData ? 'Edit Duration' : 'Add Duration' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="duration-name">Name</label>
          <input
            id="duration-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="duration-name-input"
            type="text"
            size="30"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="duration-start-date">Start Date</label>
            <DatePicker
              id="duration-start-date"
              data-testid="duration-start-date-input"
              :model-value="form.start_date"
              required
              @update:model-value="form.start_date = $event"
            />
          </div>

          <div class="add-edit-modal__form-item">
            <label for="duration-end-date">End Date</label>
            <DatePicker
              id="duration-end-date"
              data-testid="duration-end-date-input"
              :model-value="form.end_date"
              @update:model-value="form.end_date = $event"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="duration-notes">Notes</label>
          <textarea
            id="duration-notes"
            v-model="form.notes"
            data-testid="duration-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label>Color</label>
          <div class="color-picker">
            <button
              v-for="c in colorSwatches"
              :key="c.value"
              type="button"
              class="color-picker__swatch"
              :class="{ 'color-picker__swatch--selected': form.color === c.value }"
              :style="{ backgroundColor: c.value }"
              :title="c.label"
              :data-testid="`duration-color-${c.label.toLowerCase()}`"
              @click="form.color = form.color === c.value ? '' : c.value"
            ></button>
          </div>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="duration-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Duration</span>
          </button>
          <button
            type="button"
            data-testid="duration-cancel-button"
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
import type { DurationCreate, DurationUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'

const colorSwatches = [
  { value: 'var(--clr-accent-light)', label: 'Warm' },
  { value: 'var(--clr-error)', label: 'Red' },
  { value: 'var(--clr-info)', label: 'Blue' },
  { value: 'var(--clr-tertiary)', label: 'Green' },
  { value: 'var(--clr-warning)', label: 'Yellow' },
  { value: 'var(--clr-secondary)', label: 'Purple' },
  { value: 'var(--clr-accent)', label: 'Accent' },
  { value: 'var(--clr-gray-400)', label: 'Gray' },
]

const props = defineProps<{
  visible: boolean
  editData?: {
    id: number
    name: string
    start_date: string
    end_date?: string
    notes?: string
    color?: string
  } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: DurationCreate]
  update: [id: number, data: DurationUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  start_date: '',
  end_date: '',
  notes: '',
  color: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.start_date = props.editData.start_date
      form.end_date = props.editData.end_date ?? ''
      form.notes = props.editData.notes ?? ''
      form.color = props.editData.color ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.start_date = ''
  form.end_date = ''
  form.notes = ''
  form.color = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.start_date) return
  if (props.editData) {
    emit('update', props.editData.id, {
      name: form.name.trim(),
      start_date: form.start_date,
      end_date: form.end_date || undefined,
      notes: form.notes.trim() || undefined,
      color: form.color || undefined,
    })
  } else {
    emit('create', {
      name: form.name.trim(),
      start_date: form.start_date,
      end_date: form.end_date || undefined,
      notes: form.notes.trim() || undefined,
      color: form.color || undefined,
    })
  }
  handleSuccess()
}
</script>
