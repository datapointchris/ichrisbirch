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
        <h2>{{ editData ? 'Edit AutoFun Item' : 'Add AutoFun Item' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="autofun-name">Activity</label>
          <input
            id="autofun-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="autofun-name-input"
            type="text"
            class="textbox"
            placeholder="e.g. Go to XX ice cream shop"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="autofun-notes">Notes</label>
          <textarea
            id="autofun-notes"
            v-model="form.notes"
            data-testid="autofun-notes-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="autofun-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Activity</span>
          </button>
          <button
            type="button"
            data-testid="autofun-cancel-button"
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
import type { AutoFun, AutoFunCreate, AutoFunUpdate } from '@/api/types'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  editData?: AutoFun | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: AutoFunCreate]
  update: [id: number, data: AutoFunUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
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
