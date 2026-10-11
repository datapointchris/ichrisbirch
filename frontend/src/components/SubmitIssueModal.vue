<template>
  <Teleport to="body">
    <div
      id="submit-issue-background-overlay"
      :class="{ visible: visible, 'fade-out': closing }"
      @click="handleClose"
    ></div>
    <div
      id="submit-issue-window"
      :class="{ visible: visible, 'box-explode': closing }"
      @animationend="onExplodeEnd"
    >
      <form
        class="submit-issue-form"
        @submit.prevent="handleSubmit"
      >
        <h2>Submit an Issue</h2>

        <div class="submit-issue-form__item">
          <label for="issue-title">Title</label>
          <input
            id="issue-title"
            v-model="title"
            data-testid="submit-issue-title-input"
            type="text"
            size="60"
            class="textbox"
            name="title"
          />
        </div>

        <div class="submit-issue-form__item">
          <label for="issue-description">Description</label>
          <textarea
            id="issue-description"
            v-model="description"
            data-testid="submit-issue-description-input"
            rows="16"
            cols="60"
            class="textbox"
            name="description"
          ></textarea>
        </div>

        <div class="submit-issue-form__item">
          <div class="submit-issue-types">
            <label
              v-for="issueType in issueTypes"
              :key="issueType.name"
              class="submit-issue-types__wrapper"
            >
              <input
                v-model="selectedType"
                type="radio"
                name="issue-type"
                :value="issueType.name"
                :data-testid="`submit-issue-type-${issueType.name}`"
                class="submit-issue-types__input"
              />
              <span class="submit-issue-types__tile fa-2x">
                <i :class="['submit-issue-types__icon', issueType.icon]"></i>
                <span class="submit-issue-types__label">{{ issueType.name }}</span>
              </span>
            </label>
          </div>
        </div>

        <div class="submit-issue-form__buttons">
          <button
            type="submit"
            class="button"
            data-testid="submit-issue-create-button"
            :disabled="submitting"
          >
            <span class="button__text">{{ submitting ? 'Filing...' : 'File Issue' }}</span>
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
import { ApiError } from '@/api/errors'
import { useNotifications } from '@/composables/useNotifications'
import { useIssuesStore } from '@/stores/issues'
import { createLogger } from '@/utils/logger'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const logger = createLogger('SubmitIssueModal')
const { show: notify } = useNotifications()
const issues = useIssuesStore()

const title = ref('')
const description = ref('')
const selectedType = ref<string | null>(null)
const closing = ref(false)
const submitting = ref(false)

// The issue types a person files from a page. A decision is left out: it is
// filed where the choice is being made, never from a passing thought.
const issueTypes = [
  { name: 'bug', icon: 'fa-solid fa-bug' },
  { name: 'feature', icon: 'fa-regular fa-star' },
  { name: 'task', icon: 'fa-solid fa-list-check' },
  { name: 'chore', icon: 'fa-solid fa-broom' },
]

// The page and browser an issue was filed from, which a bug report needs and
// the person filing it rarely thinks to write.
function filedFrom(): string {
  return `Filed from the Submit Issue form on ${window.location.href}, in ${navigator.userAgent}.`
}

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
    const filed = await issues.create({
      title: title.value.trim(),
      description: [description.value.trim(), filedFrom()].filter(Boolean).join('\n\n'),
      repo: 'ichrisbirch',
      status: 'triage',
      ...(selectedType.value ? { type: selectedType.value } : {}),
    })
    logger.info('issue_filed', { number: filed.number })
    notify(`Issue ${filed.number} filed in triage`, 'success')
    title.value = ''
    description.value = ''
    selectedType.value = null
    handleClose()
  } catch (e) {
    const message = e instanceof ApiError ? e.userMessage : String(e)
    logger.error('issue_file_failed', { error: message })
    notify(`Failed to file issue: ${message}`, 'error')
  } finally {
    submitting.value = false
  }
}
</script>
