<template>
  <Teleport to="body">
    <div
      id="github-issue-background-overlay"
      :class="{ visible: visible, 'fade-out': closing }"
      @click="handleClose"
    ></div>
    <div
      id="github-issue-window"
      :class="{ visible: visible, 'box-explode': closing }"
      @animationend="onExplodeEnd"
    >
      <form
        class="github-issue-form"
        @submit.prevent="handleSubmit"
      >
        <h2>Submit an Issue</h2>

        <div class="github-issue-form__item">
          <label for="issue-title">Title</label>
          <input
            id="issue-title"
            v-model="title"
            type="text"
            size="60"
            class="textbox"
            name="title"
          />
        </div>

        <div class="github-issue-form__item">
          <label for="issue-description">Description</label>
          <textarea
            id="issue-description"
            v-model="description"
            rows="16"
            cols="60"
            class="textbox"
            name="description"
          ></textarea>
        </div>

        <div class="github-issue-form__item">
          <div class="github-issue-labels">
            <label
              v-for="label in issueLabels"
              :key="label.name"
              class="github-issue-labels__wrapper"
            >
              <input
                v-model="selectedLabels"
                type="checkbox"
                :value="label.name"
                class="github-issue-labels__input"
              />
              <span class="github-issue-labels__tile fa-2x">
                <i :class="['github-issue-labels__checkbox-icon', label.icon]"></i>
                <span class="github-issue-labels__checkbox-label">{{ label.name }}</span>
              </span>
            </label>
          </div>
        </div>

        <div class="github-issue-form__buttons">
          <button
            type="submit"
            class="button"
            :disabled="submitting"
          >
            <span class="button__text">{{ submitting ? 'Creating...' : 'Create Issue' }}</span>
          </button>
          <button
            type="button"
            class="button"
            @click="handleClose"
          >
            <span class="button__text">Close Window</span>
          </button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { useNotifications } from '@/composables/useNotifications'
import { createLogger } from '@/utils/logger'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const logger = createLogger('SubmitIssueModal')
const { show: notify } = useNotifications()

const title = ref('')
const description = ref('')
const selectedLabels = ref<string[]>([])
const closing = ref(false)
const submitting = ref(false)

const issueLabels = [
  { name: 'bug', icon: 'fa-solid fa-bug' },
  { name: 'docs', icon: 'fa-solid fa-file-lines' },
  { name: 'feature', icon: 'fa-regular fa-star' },
  { name: 'refactor', icon: 'fa-solid fa-code' },
]

function handleClose() {
  if (!props.visible) return
  closing.value = true
}

function onExplodeEnd(event: AnimationEvent) {
  if (event.animationName === 'box-explode') {
    closing.value = false
    emit('close')
  }
}

async function handleSubmit() {
  if (!title.value.trim()) {
    notify('Title is required', 'error')
    return
  }
  submitting.value = true
  try {
    const response = await api.post('/github/issues/', {
      title: title.value.trim(),
      description: description.value.trim() || '',
      labels: selectedLabels.value,
    })
    const { number, html_url } = response.data
    logger.info('issue_created', { number, url: html_url })
    notify(`Issue #${number} created`, 'success')
    title.value = ''
    description.value = ''
    selectedLabels.value = []
    handleClose()
  } catch (e) {
    const message = e instanceof ApiError ? e.userMessage : String(e)
    logger.error('issue_create_failed', { error: message })
    notify(`Failed to create issue: ${message}`, 'error')
  } finally {
    submitting.value = false
  }
}
</script>
