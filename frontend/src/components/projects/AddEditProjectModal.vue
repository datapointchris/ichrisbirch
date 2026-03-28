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
        <h2>{{ editData ? 'Edit Project' : 'Add Project' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="project-name">Name</label>
          <input
            id="project-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="project-name-input"
            type="text"
            size="30"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="project-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Project</span>
          </button>
          <button
            type="button"
            data-testid="project-cancel-button"
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
import type { ProjectCreate, ProjectUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  editData?: { id: number; name: string } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: ProjectCreate]
  update: [id: number, data: ProjectUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
    }
  }
)

function resetForm() {
  form.name = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, { name: form.name.trim() })
  } else {
    emit('create', { name: form.name.trim() })
  }
  handleSuccess()
}
</script>
