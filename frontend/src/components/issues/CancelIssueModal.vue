<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="reasonInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>Cancel #{{ issue?.number }}</h2>

        <p class="issue-modal__note">{{ issue?.title }} closes without being done. Say why, or name the issue that already covers it.</p>

        <div class="add-edit-modal__form-item">
          <label for="issue-cancel-reason">Why it will not be done</label>
          <textarea
            id="issue-cancel-reason"
            ref="reasonInput"
            v-model="reason"
            data-testid="issue-cancel-reason-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="issue-duplicate-of">Duplicate of</label>
          <input
            id="issue-duplicate-of"
            v-model="duplicateOf"
            data-testid="issue-duplicate-of-input"
            type="text"
            class="textbox"
            :class="{ 'textbox--error': errors.duplicateOf }"
            placeholder="#812"
            @input="clearError('duplicateOf')"
          />
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="issue-cancel-submit-button"
            class="button button--danger"
            :disabled="!reason.trim() && !duplicateOf.trim()"
          >
            <span class="button__text button__text--danger">Cancel Issue</span>
          </button>
          <button
            type="button"
            class="button"
            @click="handleClose()"
          >
            <span class="button__text">Keep It</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Issue, IssueUpdate } from '@/api/client'
import { useFieldErrors } from '@/composables/useFieldErrors'
import AddEditModal from '@/components/AddEditModal.vue'
import { parseIssueNumber } from '@/components/issues/issueNumbers'

defineProps<{
  visible: boolean
  issue: Issue | null
}>()

const emit = defineEmits<{
  close: []
  cancel: [closure: Pick<IssueUpdate, 'status_reason' | 'duplicate_of'>]
}>()

const { errors, validate, clearError } = useFieldErrors()
const reasonInput = ref<HTMLTextAreaElement | null>(null)
const reason = ref('')
const duplicateOf = ref('')

function handleModalClose() {
  reason.value = ''
  duplicateOf.value = ''
  emit('close')
}

// The API refuses a cancel with neither: a canceled issue nobody explained
// reads as forgotten, and the same work gets filed again.
function handleSubmit(handleSuccess: () => void) {
  const duplicate = duplicateOf.value.trim() ? parseIssueNumber(duplicateOf.value) : null
  const valid = validate({
    duplicateOf: duplicateOf.value.trim() && duplicate === null ? `"${duplicateOf.value.trim()}" is not an issue number` : null,
  })
  if (!valid || (!reason.value.trim() && duplicate === null)) return
  const closure: Pick<IssueUpdate, 'status_reason' | 'duplicate_of'> = {}
  if (reason.value.trim()) closure.status_reason = reason.value.trim()
  if (duplicate !== null) closure.duplicate_of = duplicate
  emit('cancel', closure)
  handleSuccess()
}
</script>
