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

        <div class="add-edit-modal__form-item">
          <label for="project-description">Description</label>
          <textarea
            id="project-description"
            v-model="form.description"
            data-testid="project-description-input"
            rows="3"
            class="textbox"
          ></textarea>
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
  editData?: { id: string; name: string; description?: string } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: ProjectCreate]
  update: [id: string, data: ProjectUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  description: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.description = props.editData.description ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.description = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
    })
  } else {
    emit('create', {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
    })
  }
  handleSuccess()
}
</script>
