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
        <h2>{{ editData ? 'Edit AutoTask' : 'Add AutoTask' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="autotask-name">Name</label>
          <input
            id="autotask-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="autotask-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="autotask-window">Window (days)</label>
            <input
              id="autotask-window"
              v-model="form.windowDays"
              data-testid="autotask-window-input"
              type="number"
              min="1"
              placeholder="Category default"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="autotask-anchor">Next copy counts from</label>
            <NeuSelect
              :model-value="form.anchor"
              :options="anchorOptions"
              data-testid="autotask-anchor-input"
              @update:model-value="form.anchor = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="autotask-category">Category</label>
            <NeuSelect
              :model-value="form.category"
              :options="categoryOptions"
              data-testid="autotask-category-input"
              @update:model-value="form.category = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="autotask-frequency">Frequency</label>
            <NeuSelect
              :model-value="form.frequency"
              :options="frequencyOptions"
              data-testid="autotask-frequency-input"
              @update:model-value="form.frequency = $event"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="autotask-notes">Notes</label>
          <textarea
            id="autotask-notes"
            v-model="form.notes"
            data-testid="autotask-notes-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="autotask-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} AutoTask</span>
          </button>
          <button
            type="button"
            data-testid="autotask-cancel-button"
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
import type { AutoTask, AutoTaskAnchor, AutoTaskCreate, AutoTaskUpdate, TaskCategory, AutoTaskFrequency } from '@/api/client'
import { TASK_CATEGORIES, AUTOTASK_FREQUENCIES, AUTOTASK_ANCHORS } from '@/stores/autotasks'
import NeuSelect from '@/components/NeuSelect.vue'

const categoryOptions = TASK_CATEGORIES.map((c) => ({ value: c, label: c }))
const frequencyOptions = AUTOTASK_FREQUENCIES.map((f) => ({ value: f, label: f }))
const anchorOptions = AUTOTASK_ANCHORS
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  editData?: AutoTask | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: AutoTaskCreate]
  update: [id: number, data: AutoTaskUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  windowDays: '' as number | '',
  anchor: 'completion' as AutoTaskAnchor,
  category: 'Chore' as TaskCategory,
  frequency: 'Monthly' as AutoTaskFrequency,
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.windowDays = props.editData.window_days ?? ''
      form.anchor = props.editData.anchor
      form.category = props.editData.category
      form.frequency = props.editData.frequency
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.windowDays = ''
  form.anchor = 'completion'
  form.category = 'Chore'
  form.frequency = 'Monthly'
  form.notes = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  const windowDays = Number(form.windowDays)
  const data = {
    name: form.name.trim(),
    // null clears an edited template back to its category's window
    window_days: form.windowDays !== '' && windowDays >= 1 ? windowDays : null,
    anchor: form.anchor,
    category: form.category,
    frequency: form.frequency,
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
