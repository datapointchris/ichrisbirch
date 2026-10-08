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
        <h2>Drop {{ taskName }}</h2>

        <p class="drop-task-modal__note">Dropping takes the task off the list without completing it. Snooze is the way to say "not now".</p>

        <div class="add-edit-modal__form-item">
          <label for="task-drop-reason">Why is it dropped? (optional)</label>
          <textarea
            id="task-drop-reason"
            ref="reasonInput"
            v-model="reason"
            data-testid="task-drop-reason-input"
            rows="4"
            class="textbox drop-task-modal__reason-input"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="task-drop-submit-button"
            class="button button--danger"
          >
            <span class="button__text button__text--danger">Drop Task</span>
          </button>
          <button
            type="button"
            data-testid="task-drop-cancel-button"
            class="button"
            @click="handleClose()"
          >
            <span class="button__text">Cancel</span>
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
  taskName: string
}>()

const emit = defineEmits<{
  close: []
  drop: [reason: string | undefined]
}>()

const reasonInput = ref<HTMLTextAreaElement | null>(null)
const reason = ref('')

function handleModalClose() {
  reason.value = ''
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  emit('drop', reason.value.trim() || undefined)
  handleSuccess()
}
</script>

<style scoped lang="scss">
.drop-task-modal__note {
  max-width: 400px;
}

.drop-task-modal__reason-input {
  min-width: 400px;
  resize: vertical;
}
</style>
