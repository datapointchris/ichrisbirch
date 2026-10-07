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
        <h2>Add New Task</h2>

        <div class="add-edit-modal__form-item">
          <label for="add-task-name">Name</label>
          <input
            id="add-task-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="task-name-input"
            type="text"
            size="50"
            class="textbox"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label>Category</label>
          <div class="add-edit-modal__tiles">
            <template
              v-for="cat in categories"
              :key="cat"
            >
              <input
                :id="'cat-' + cat"
                v-model="form.category"
                type="radio"
                class="add-edit-modal__tile-input"
                :value="cat"
              />
              <label
                :for="'cat-' + cat"
                class="add-edit-modal__tile"
                :data-testid="'task-category-tile-' + cat"
              >
                {{ cat }}
              </label>
            </template>
          </div>
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="add-task-window">Window (days)</label>
            <input
              id="add-task-window"
              v-model="form.windowDays"
              data-testid="task-window-input"
              type="number"
              min="1"
              placeholder="Category default"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <button
              type="button"
              data-testid="task-pin-to-top-button"
              class="button"
              :aria-pressed="form.pinned"
              @click="form.pinned = !form.pinned"
            >
              <span class="button__text">{{ form.pinned ? 'Pinned to Top' : 'Pin to Top' }}</span>
            </button>
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="add-task-notes">Notes</label>
          <textarea
            id="add-task-notes"
            v-model="form.notes"
            rows="3"
            cols="50"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="task-submit-button"
            class="button"
          >
            <span class="button__text">Add Task</span>
          </button>
          <button
            type="button"
            data-testid="task-cancel-button"
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
import { reactive, ref } from 'vue'
import type { TaskCategory, TaskCreate } from '@/api/client'
import { TASK_CATEGORIES } from '@/stores/tasks'
import AddEditModal from '@/components/AddEditModal.vue'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [data: TaskCreate]
}>()

const categories = TASK_CATEGORIES
const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  category: '' as TaskCategory | '',
  windowDays: '' as number | '',
  pinned: false,
  notes: '',
})

function handleModalClose() {
  form.name = ''
  form.notes = ''
  form.category = ''
  form.windowDays = ''
  form.pinned = false
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.category) return
  const windowDays = Number(form.windowDays)
  emit('create', {
    name: form.name.trim(),
    category: form.category as TaskCategory,
    window_days: form.windowDays !== '' && windowDays >= 1 ? windowDays : undefined,
    pinned: form.pinned,
    notes: form.notes.trim() || undefined,
  })
  handleSuccess()
}
</script>
