<template>
  <div
    class="issues__detail issues__detail--open"
    data-testid="issue-detail"
  >
    <div
      v-if="issue.description"
      class="issues__detail-field issues__detail-notes"
    >
      <span class="issues__detail-field-label">Description</span>
      <div
        class="issues__detail-field-value markdown-body"
        v-html="renderMarkdown(issue.description)"
      ></div>
    </div>
    <div
      v-if="issue.acceptance"
      class="issues__detail-field issues__detail-notes"
    >
      <span class="issues__detail-field-label">Done when</span>
      <div
        class="issues__detail-field-value markdown-body"
        v-html="renderMarkdown(issue.acceptance)"
      ></div>
    </div>

    <div
      v-for="field in fields"
      :key="field.label"
      class="issues__detail-field"
    >
      <span class="issues__detail-field-label">{{ field.label }}</span>
      <span class="issues__detail-field-value">{{ field.value }}</span>
    </div>

    <div
      v-if="issue.status === 'in_progress'"
      class="issues__detail-field"
    >
      <span class="issues__detail-field-label">Working</span>
      <span class="issues__detail-field-value">{{ claimLine }}</span>
    </div>

    <div class="issues__detail-field issues__detail-notes">
      <span class="issues__detail-field-label">Waits on</span>
      <div class="issues__detail-field-value issues__links">
        <span
          v-for="dependency in issue.depends_on"
          :key="dependency.id"
          class="issues__link"
          :class="{ 'issues__link--closed': isClosedIssue(dependency) }"
          data-testid="issue-dependency"
        >
          {{ summaryLine(dependency) }}
          <button
            type="button"
            class="issues__link-remove"
            :title="`Stop waiting on #${dependency.number}`"
            data-testid="issue-dependency-remove"
            @click="removeDependency(dependency)"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </span>
        <form
          class="issues__inline-form"
          @submit.prevent="addDependency"
        >
          <input
            v-model="newDependency"
            type="text"
            class="textbox"
            :class="{ 'textbox--error': errors.dependency }"
            placeholder="#812"
            data-testid="issue-dependency-input"
            @input="clearError('dependency')"
          />
          <button
            type="submit"
            class="button button--small"
            data-testid="issue-dependency-add"
            :disabled="!newDependency.trim()"
          >
            <span class="button__text">Wait on</span>
          </button>
        </form>
      </div>
    </div>

    <div
      v-if="issue.blocks.length > 0"
      class="issues__detail-field issues__detail-notes"
    >
      <span class="issues__detail-field-label">Holds up</span>
      <div class="issues__detail-field-value issues__links">
        <span
          v-for="blocked in issue.blocks"
          :key="blocked.id"
          class="issues__link"
          :class="{ 'issues__link--closed': isClosedIssue(blocked) }"
          >{{ summaryLine(blocked) }}</span
        >
      </div>
    </div>

    <div
      v-if="detail && detail.children.length > 0"
      class="issues__detail-field issues__detail-notes"
    >
      <span class="issues__detail-field-label">Children</span>
      <div class="issues__detail-field-value issues__links">
        <span
          v-for="child in detail.children"
          :key="child.id"
          class="issues__link"
          :class="{ 'issues__link--closed': isClosedIssue(child) }"
          >{{ summaryLine(child) }}</span
        >
      </div>
    </div>

    <div class="issues__detail-field issues__detail-notes">
      <span class="issues__detail-field-label">Comments</span>
      <div
        v-if="!detail"
        class="issues__empty"
      >
        Loading...
      </div>
      <template v-else>
        <div
          v-for="comment in detail.comments"
          :key="comment.id"
          class="issues__comment"
          data-testid="issue-comment"
        >
          <div class="issues__comment-meta">
            <span>{{ comment.author ?? 'unsigned' }}</span>
            <span>{{ formatDate(comment.created_ts, 'dateTime') }}</span>
            <button
              type="button"
              class="issues__link-remove"
              title="Delete comment"
              data-testid="issue-comment-remove"
              @click="removeComment(comment)"
            >
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div
            class="markdown-body"
            v-html="renderMarkdown(comment.body)"
          ></div>
        </div>
        <div
          v-if="detail.comments.length === 0"
          class="issues__empty"
        >
          No comments.
        </div>
        <form
          class="issues__comment-form"
          @submit.prevent="addComment"
        >
          <textarea
            v-model="newComment"
            rows="2"
            class="textbox"
            placeholder="What was found, decided or tried"
            data-testid="issue-comment-input"
          ></textarea>
          <button
            type="submit"
            class="button button--small"
            data-testid="issue-comment-add"
            :disabled="!newComment.trim()"
          >
            <span class="button__text">Comment</span>
          </button>
        </form>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Issue, IssueComment, IssueDetail, IssueSummary } from '@/api/client'
import { useIssuesStore, isClosedIssue, ISSUE_STATUS_LABELS } from '@/stores/issues'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { useFieldErrors } from '@/composables/useFieldErrors'
import { formatDate } from '@/composables/formatDate'
import { renderMarkdown } from '@/utils/markdown'
import { ApiError } from '@/api/errors'
import { parseIssueNumber } from '@/components/issues/issueNumbers'

const props = defineProps<{
  issue: Issue
  detail: IssueDetail | null
}>()

const store = useIssuesStore()
const auth = useAuthStore()
const { show: notify } = useNotifications()
const { errors, validate, clearError } = useFieldErrors()

const newDependency = ref('')
const newComment = ref('')

function summaryLine(summary: IssueSummary): string {
  return `#${summary.number} ${summary.title}`
}

const claimLine = computed(() => {
  if (!props.issue.claimed_by || !props.issue.claim_expires_ts) return 'by hand, with no claim to expire'
  return `${props.issue.claimed_by} until ${formatDate(props.issue.claim_expires_ts, 'dateTime')}`
})

const fields = computed(() => {
  const issue = props.issue
  const rows: { label: string; value: string }[] = []
  if (issue.status_reason) rows.push({ label: ISSUE_STATUS_LABELS[issue.status], value: issue.status_reason })
  if (issue.duplicate_of) rows.push({ label: 'Duplicate of', value: summaryLine(issue.duplicate_of) })
  if (issue.initiative) rows.push({ label: 'Initiative', value: issue.initiative.name })
  if (issue.parent) rows.push({ label: 'Parent', value: summaryLine(issue.parent) })
  if (issue.discovered_from) rows.push({ label: 'Found while on', value: summaryLine(issue.discovered_from) })
  if (issue.labels.length > 0) rows.push({ label: 'Labels', value: issue.labels.join(', ') })
  if (issue.deferred_until_date) rows.push({ label: 'Not before', value: formatDate(issue.deferred_until_date, 'shortDate') })
  rows.push({ label: 'Filed', value: formatDate(issue.created_ts, 'dateTime') })
  rows.push({ label: 'Updated', value: formatDate(issue.updated_ts, 'dateTime') })
  if (issue.closed_ts) rows.push({ label: 'Closed', value: formatDate(issue.closed_ts, 'dateTime') })
  return rows
})

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`${action} failed: ${detail}`, 'error')
}

async function addDependency() {
  const number = parseIssueNumber(newDependency.value)
  if (!validate({ dependency: number === null ? `"${newDependency.value.trim()}" is not an issue number` : null })) return
  try {
    await store.addDependency(props.issue, number!)
    newDependency.value = ''
    notify(`#${props.issue.number} waits on #${number} | added`, 'success')
  } catch (e) {
    failure('Adding the dependency', e)
  }
}

async function removeDependency(dependency: IssueSummary) {
  try {
    await store.removeDependency(props.issue, dependency)
    notify(`#${props.issue.number} no longer waits on #${dependency.number} | deleted`, 'success')
  } catch (e) {
    failure('Removing the dependency', e)
  }
}

async function addComment() {
  const body = newComment.value.trim()
  if (!body) return
  try {
    await store.addComment(props.issue, body, auth.user?.name)
    newComment.value = ''
    notify(`Comment on #${props.issue.number} | added`, 'success')
  } catch (e) {
    failure('Commenting', e)
  }
}

async function removeComment(comment: IssueComment) {
  try {
    await store.removeComment(props.issue, comment)
    notify(`Comment on #${props.issue.number} | deleted`, 'success')
  } catch (e) {
    failure('Deleting the comment', e)
  }
}
</script>
