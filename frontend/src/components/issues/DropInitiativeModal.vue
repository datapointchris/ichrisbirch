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
        <h2>Drop {{ initiativeName }}</h2>

        <p class="issue-modal__note">
          Dropping closes the initiative without pretending it was reached. Its issues stay exactly as they are.
        </p>

        <div class="add-edit-modal__form-item">
          <label for="initiative-drop-reason">Why it is dropped</label>
          <textarea
            id="initiative-drop-reason"
            ref="reasonInput"
            v-model="reason"
            data-testid="initiative-drop-reason-input"
            rows="3"
            class="textbox"
            required
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="initiative-drop-submit-button"
            class="button button--danger"
            :disabled="!reason.trim()"
          >
            <span class="button__text button__text--danger">Drop Initiative</span>
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
import AddEditModal from '@/components/AddEditModal.vue'

defineProps<{
  visible: boolean
  initiativeName: string
}>()

const emit = defineEmits<{
  close: []
  drop: [reason: string]
}>()

const reasonInput = ref<HTMLTextAreaElement | null>(null)
const reason = ref('')

function handleModalClose() {
  reason.value = ''
  emit('close')
}

// The API refuses a drop with no reason, because a dropped initiative nobody
// explained reads as one that stalled and invites the same plan back.
function handleSubmit(handleSuccess: () => void) {
  if (!reason.value.trim()) return
  emit('drop', reason.value.trim())
  handleSuccess()
}
</script>
