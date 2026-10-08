<template>
  <div>
    <AppSubnav :links="subnavLinks">
      <button
        data-testid="initiative-add-button"
        class="button"
        @click="openCreate"
      >
        <span class="button__text">Start Initiative</span>
      </button>
    </AppSubnav>

    <div class="grid grid--one-column grid--tight">
      <div class="issues__filters">
        <NeuSelect
          :model-value="store.statusFilter"
          :options="statusOptions"
          data-testid="initiative-status-filter"
          @update:model-value="applyStatus($event)"
        />
      </div>
    </div>

    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="issue-initiatives__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div
            class="issue-initiatives__header"
            data-testid="initiatives-header"
          >
            <span>Initiative</span>
            <span>Priority</span>
            <span>Status</span>
            <span>Open</span>
            <span>Done</span>
            <span>Canceled</span>
            <span>Repos</span>
            <span>Actions</span>
          </div>

          <div
            v-if="store.items.length === 0"
            class="issue-initiatives__empty"
            data-testid="initiative-empty"
          >
            {{ emptyMessage }}
          </div>

          <template
            v-for="initiative in store.items"
            :key="initiative.id"
          >
            <div
              data-testid="initiative-item"
              class="issue-initiatives__row"
              :class="[`issue--p${initiative.priority}`, { 'issue--closed': initiative.status !== 'active' }]"
            >
              <span>
                <RouterLink
                  :to="issuesLink(initiative)"
                  class="issue-initiatives__link"
                  data-testid="initiative-issues-link"
                  >{{ initiative.name }}</RouterLink
                >
              </span>
              <span>{{ priorityLabel(issues.vocabulary, initiative.priority) }}</span>
              <span>{{ INITIATIVE_STATUS_LABELS[initiative.status] }}</span>
              <span>{{ initiative.open_count }}</span>
              <span>{{ initiative.completed_count }}</span>
              <span>{{ initiative.canceled_count }}</span>
              <span :title="initiative.repos.join(', ')">{{ initiative.repos.join(', ') || '—' }}</span>
              <span class="issue-initiatives__actions">
                <ActionButton
                  icon="fa-solid fa-chevron-down"
                  title="Toggle details"
                  :rotated="expandedId === initiative.id"
                  @click="toggle(initiative.id)"
                />
                <ActionButton
                  v-if="initiative.status === 'active'"
                  icon="fa-solid fa-check"
                  variant="success"
                  title="Complete — the outcome is reached"
                  data-testid="initiative-complete-button"
                  @click="transition(initiative, 'completed', 'completed')"
                />
                <ActionButton
                  v-if="initiative.status === 'active'"
                  icon="fa-solid fa-ban"
                  variant="warning"
                  title="Drop — closed without being reached"
                  data-testid="initiative-drop-button"
                  @click="dropTarget = initiative"
                />
                <ActionButton
                  v-else
                  icon="fa-solid fa-rotate-left"
                  variant="success"
                  title="Reopen"
                  data-testid="initiative-reopen-button"
                  @click="transition(initiative, 'active', 'reopened')"
                />
                <ActionButton
                  icon="fa-solid fa-pen-to-square"
                  variant="warning"
                  title="Edit initiative"
                  data-testid="initiative-edit-button"
                  @click="openEdit(initiative)"
                />
                <ActionButton
                  icon="fa-regular fa-trash-can"
                  variant="danger"
                  title="Delete initiative — its issues stay, without it"
                  data-testid="initiative-delete-button"
                  @click="handleDelete(initiative)"
                />
              </span>
            </div>

            <div
              class="issue-initiatives__detail"
              :class="{ 'issue-initiatives__detail--open': expandedId === initiative.id }"
            >
              <div
                v-if="initiative.description"
                class="issue-initiatives__detail-field issue-initiatives__detail-notes"
              >
                <span class="issue-initiatives__detail-field-label">Description</span>
                <span class="issue-initiatives__detail-field-value">{{ initiative.description }}</span>
              </div>
              <div
                v-if="initiative.status_reason"
                class="issue-initiatives__detail-field issue-initiatives__detail-notes"
              >
                <span class="issue-initiatives__detail-field-label">Why it was dropped</span>
                <span class="issue-initiatives__detail-field-value">{{ initiative.status_reason }}</span>
              </div>
              <div class="issue-initiatives__detail-field">
                <span class="issue-initiatives__detail-field-label">Started</span>
                <span class="issue-initiatives__detail-field-value">{{ formatDate(initiative.created_ts, 'shortDate') }}</span>
              </div>
              <div
                v-if="initiative.closed_ts"
                class="issue-initiatives__detail-field"
              >
                <span class="issue-initiatives__detail-field-label">Closed</span>
                <span class="issue-initiatives__detail-field-value">{{ formatDate(initiative.closed_ts, 'shortDate') }}</span>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>

    <AddEditInitiativeModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />

    <DropInitiativeModal
      :visible="dropTarget !== null"
      :initiative-name="dropTarget?.name ?? ''"
      @close="dropTarget = null"
      @drop="handleDrop"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Initiative, InitiativeCreate, InitiativeStatus, InitiativeUpdate } from '@/api/client'
import { useIssueInitiativesStore, INITIATIVE_STATUS_LABELS, type InitiativeStatusFilter } from '@/stores/issueInitiatives'
import { useIssuesStore, priorityLabel } from '@/stores/issues'
import { useNotifications } from '@/composables/useNotifications'
import { formatDate } from '@/composables/formatDate'
import { ApiError } from '@/api/errors'
import ActionButton from '@/components/ActionButton.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import AddEditInitiativeModal from '@/components/issues/AddEditInitiativeModal.vue'
import DropInitiativeModal from '@/components/issues/DropInitiativeModal.vue'
import { ISSUES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = ISSUES_SUBNAV
const store = useIssueInitiativesStore()
const issues = useIssuesStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<Initiative | null>(null)
const dropTarget = ref<Initiative | null>(null)
const expandedId = ref<string | null>(null)

const statusOptions: { value: InitiativeStatusFilter; label: string }[] = [
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'dropped', label: 'Dropped' },
  { value: 'all', label: 'Every Status' },
]

const emptyMessage = computed(() =>
  store.statusFilter === 'all' ? 'No initiatives yet. Start one!' : `No ${store.statusFilter} initiatives.`
)

// An active initiative links to the work left in it; a finished one to all of it.
function issuesLink(initiative: Initiative) {
  const query: Record<string, string> = { initiative: initiative.name }
  if (initiative.status !== 'active') query.status = 'all'
  return { path: '/issues', query }
}

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`${action} failed: ${detail}`, 'error')
}

onMounted(async () => {
  try {
    await Promise.all([store.fetchAll(), issues.fetchVocabulary()])
  } catch (e) {
    failure('Loading initiatives', e)
  }
})

async function applyStatus(status: InitiativeStatusFilter) {
  try {
    await store.setStatusFilter(status)
  } catch (e) {
    failure('Filtering', e)
  }
}

function toggle(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function openCreate() {
  editTarget.value = null
  showModal.value = true
}

function openEdit(initiative: Initiative) {
  editTarget.value = initiative
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: InitiativeCreate) {
  try {
    await store.create(data)
    notify(`${data.name} | added`, 'success')
  } catch (e) {
    failure('Starting the initiative', e)
  }
}

async function handleUpdate(initiative: Initiative, data: InitiativeUpdate) {
  try {
    await store.update(initiative, data)
    notify(`${initiative.name} updated`, 'success')
  } catch (e) {
    failure('Update', e)
  }
}

async function transition(initiative: Initiative, status: InitiativeStatus, done: string) {
  try {
    await store.setStatus(initiative, status)
    notify(`${initiative.name} ${done}`, 'success')
  } catch (e) {
    failure(initiative.name, e)
  }
}

async function handleDrop(reason: string) {
  const initiative = dropTarget.value
  dropTarget.value = null
  if (!initiative) return
  try {
    await store.setStatus(initiative, 'dropped', reason)
    notify(`${initiative.name} dropped`, 'success')
  } catch (e) {
    failure('Drop', e)
  }
}

async function handleDelete(initiative: Initiative) {
  try {
    await store.remove(initiative)
    notify(`${initiative.name} | deleted`, 'success')
  } catch (e) {
    failure('Delete', e)
  }
}
</script>
