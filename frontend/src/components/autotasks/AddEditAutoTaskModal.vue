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
            <label for="autotask-priority">Priority</label>
            <input
              id="autotask-priority"
              v-model="form.priority"
              data-testid="autotask-priority-input"
              type="number"
              min="1"
              class="textbox add-edit-modal__number-input"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="autotask-category">Category</label>
            <select
              id="autotask-category"
              v-model="form.category"
              data-testid="autotask-category-input"
              class="textbox"
            >
              <option
                v-for="cat in TASK_CATEGORIES"
                :key="cat"
                :value="cat"
              >
                {{ cat }}
              </option>
            </select>
          </div>
          <div class="add-edit-modal__form-item">
            <label for="autotask-frequency">Frequency</label>
            <select
              id="autotask-frequency"
              v-model="form.frequency"
              data-testid="autotask-frequency-input"
              class="textbox"
            >
              <option
                v-for="freq in AUTOTASK_FREQUENCIES"
                :key="freq"
                :value="freq"
              >
                {{ freq }}
              </option>
            </select>
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
import type { AutoTask, AutoTaskCreate, AutoTaskUpdate, TaskCategory, AutoTaskFrequency } from '@/api/client'
import { TASK_CATEGORIES, AUTOTASK_FREQUENCIES } from '@/stores/autotasks'
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
  priority: 1,
  category: 'Chore' as TaskCategory,
  frequency: 'Monthly' as AutoTaskFrequency,
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.priority = props.editData.priority
      form.category = props.editData.category
      form.frequency = props.editData.frequency
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.priority = 1
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
  const data = {
    name: form.name.trim(),
    priority: Number(form.priority),
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
