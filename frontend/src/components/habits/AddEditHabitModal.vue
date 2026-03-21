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
        <h2>{{ editData ? 'Edit Habit' : 'Add Habit' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="habit-name">Name</label>
          <input
            id="habit-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="habit-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="habit-category">Category</label>
          <select
            id="habit-category"
            v-model="form.category_id"
            data-testid="habit-category-input"
            class="textbox"
            required
          >
            <option
              value=""
              disabled
            >
              Select a category
            </option>
            <option
              v-for="cat in categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="habit-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Habit</span>
          </button>
          <button
            type="button"
            data-testid="habit-cancel-button"
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
import type { HabitCreate, HabitUpdate, HabitCategory } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  categories: HabitCategory[]
  editData?: {
    id: number
    name: string
    category_id: number
  } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: HabitCreate]
  update: [id: number, data: HabitUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  category_id: '' as string | number,
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.category_id = props.editData.category_id
    }
  }
)

function resetForm() {
  form.name = ''
  form.category_id = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.category_id) return
  if (props.editData) {
    emit('update', props.editData.id, {
      name: form.name.trim(),
      category_id: Number(form.category_id),
    })
  } else {
    emit('create', {
      name: form.name.trim(),
      category_id: Number(form.category_id),
    })
  }
  handleSuccess()
}
</script>
