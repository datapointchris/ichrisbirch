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
        <h2>{{ editData ? 'Edit Initiative' : 'Start an Initiative' }}</h2>

        <p
          v-if="!editData"
          class="issue-modal__note"
        >
          An initiative is one outcome several issues add up to. It finishes, so name what done looks like.
        </p>

        <div class="add-edit-modal__form-item">
          <label for="initiative-name">Name</label>
          <input
            id="initiative-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="initiative-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label>Priority</label>
          <NeuSelect
            :model-value="form.priority"
            :options="priorityOptions"
            data-testid="initiative-priority-input"
            @update:model-value="form.priority = $event"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="initiative-description">Description</label>
          <textarea
            id="initiative-description"
            v-model="form.description"
            data-testid="initiative-description-input"
            rows="4"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="initiative-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Start' }} Initiative</span>
          </button>
          <button
            type="button"
            data-testid="initiative-cancel-button"
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
import { computed, reactive, ref, watch } from 'vue'
import type { Initiative, InitiativeCreate, InitiativeUpdate } from '@/api/client'
import { useIssuesStore } from '@/stores/issues'
import AddEditModal from '@/components/AddEditModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const props = defineProps<{
  visible: boolean
  editData?: Initiative | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: InitiativeCreate]
  update: [initiative: Initiative, data: InitiativeUpdate]
}>()

const issues = useIssuesStore()
const nameInput = ref<HTMLInputElement | null>(null)

const priorityOptions = computed(() => issues.vocabulary.priorities.map((entry) => ({ value: entry.value, label: entry.name })))

function createEmptyForm() {
  return { name: '', priority: 0, description: '' }
}

const form = reactive(createEmptyForm())

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      Object.assign(form, {
        name: props.editData.name,
        priority: props.editData.priority,
        description: props.editData.description ?? '',
      })
    } else if (val) {
      Object.assign(form, createEmptyForm())
    }
  }
)

function handleModalClose() {
  Object.assign(form, createEmptyForm())
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  const name = form.name.trim()
  if (!name) return
  const description = form.description.trim()
  if (props.editData) {
    emit('update', props.editData, { name, priority: form.priority, description: description || null })
  } else {
    const payload: InitiativeCreate = { name, priority: form.priority }
    if (description) payload.description = description
    emit('create', payload)
  }
  handleSuccess()
}
</script>
