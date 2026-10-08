<template>
  <div>
    <AppSubnav :links="subnavLinks">
      <button
        data-testid="issue-add-button"
        class="button"
        @click="openCreate"
      >
        <span class="button__text">File Issue</span>
      </button>
    </AppSubnav>

    <div class="grid grid--one-column grid--tight">
      <div
        class="task-layout__info"
        data-testid="issues-info"
      >
        <span
          v-for="name in ISSUE_LENSES"
          :key="name"
          class="task-layout__count issue-lens"
          :class="{
            'issue-lens--active': store.lens === name,
            'issue-lens--attention': name === 'decisions' && store.lensCounts.decisions > 0,
          }"
          :data-testid="`issue-lens-${name}`"
          @click="store.setLens(name)"
          >{{ ISSUE_LENS_LABELS[name] }}: {{ store.lensCounts[name] }}</span
        >
      </div>
    </div>

    <div class="grid grid--one-column grid--tight">
      <div class="issues__filters">
        <NeuSelect
          :model-value="store.statusFilter"
          :options="statusOptions"
          data-testid="issue-status-filter"
          @update:model-value="applyFilter('status', $event)"
        />
        <NeuSelect
          :model-value="store.repoFilter"
          :options="repoOptions"
          data-testid="issue-repo-filter"
          @update:model-value="applyFilter('repo', $event)"
        />
        <NeuSelect
          :model-value="store.typeFilter"
          :options="typeOptions"
          data-testid="issue-type-filter"
          @update:model-value="applyFilter('type', $event)"
        />
        <NeuSelect
          :model-value="store.labelFilter"
          :options="labelOptions"
          data-testid="issue-label-filter"
          @update:model-value="applyFilter('label', $event)"
        />
        <NeuSelect
          :model-value="store.initiativeFilter"
          :options="initiativeOptions"
          data-testid="issue-initiative-filter"
          @update:model-value="applyFilter('initiative', $event)"
        />
        <NeuSelect
          :model-value="store.priorityFilter"
          :options="priorityOptions"
          data-testid="issue-priority-filter"
          @update:model-value="applyFilter('priority', $event)"
        />
        <form
          class="issues__search"
          @submit.prevent="applySearch"
        >
          <input
            v-model="searchText"
            type="text"
            class="textbox"
            placeholder="Search titles and descriptions"
            data-testid="issue-search-input"
          />
          <button
            type="submit"
            class="button button--small"
            data-testid="issue-search-button"
          >
            <span class="button__text"><i class="fa-solid fa-search"></i></span>
          </button>
        </form>
      </div>
    </div>

    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="issues__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div
            class="issues__header"
            data-testid="issues-header"
          >
            <span>#</span>
            <span>Priority</span>
            <span>Type</span>
            <span>Status</span>
            <span>Repo</span>
            <span>Title</span>
            <span>Actions</span>
          </div>

          <div
            v-if="store.visibleItems.length === 0"
            class="issues__empty"
            data-testid="issue-empty"
          >
            {{ emptyMessage }}
          </div>

          <template
            v-for="(issue, index) in store.visibleItems"
            :key="issue.id"
          >
            <div
              data-testid="issue-item"
              class="issues__row"
              :class="[`issue--p${issue.effective_priority}`, { 'issue--closed': isClosedIssue(issue) }]"
            >
              <span class="issues__number">{{ issue.number }}</span>
              <span :title="priorityTitle(issue)">{{ priorityCell(issue) }}</span>
              <span>{{ issue.type }}</span>
              <span>{{ ISSUE_STATUS_LABELS[issue.status] }}</span>
              <span>{{ issue.repo ?? '—' }}</span>
              <span
                class="issues__title"
                :title="issue.title"
              >
                {{ issue.title }}
                <span
                  v-for="label in issue.labels"
                  :key="label"
                  class="issues__label"
                  >{{ label }}</span
                >
                <span
                  v-for="note in stateNotes(issue)"
                  :key="note"
                  class="issues__note"
                  data-testid="issue-note"
                  >{{ note }}</span
                >
              </span>
              <span class="issues__actions">
                <ActionButton
                  icon="fa-solid fa-chevron-down"
                  title="Toggle details"
                  data-testid="issue-toggle-button"
                  :rotated="store.expandedId === issue.id"
                  @click="toggle(issue)"
                />
                <ActionButton
                  v-if="neighbor(index, -1)"
                  icon="fa-solid fa-arrow-up"
                  title="Move above the issue before it"
                  data-testid="issue-move-up-button"
                  @click="moveIssue(issue, { before: neighbor(index, -1)!.number })"
                />
                <ActionButton
                  v-if="neighbor(index, 1)"
                  icon="fa-solid fa-arrow-down"
                  title="Move below the issue after it"
                  data-testid="issue-move-down-button"
                  @click="moveIssue(issue, { after: neighbor(index, 1)!.number })"
                />
                <ActionButton
                  v-if="issue.status === 'triage'"
                  icon="fa-solid fa-inbox"
                  variant="success"
                  title="Accept — take it out of triage as open work"
                  data-testid="issue-accept-button"
                  @click="transition(issue, 'open', 'accepted')"
                />
                <ActionButton
                  v-if="issue.status === 'open'"
                  icon="fa-solid fa-play"
                  title="Start — work it by hand"
                  data-testid="issue-start-button"
                  @click="transition(issue, 'in_progress', 'started')"
                />
                <ActionButton
                  v-if="issue.status === 'in_progress'"
                  icon="fa-solid fa-hand"
                  title="Release — back to the queue"
                  data-testid="issue-release-button"
                  @click="release(issue)"
                />
                <ActionButton
                  v-if="!isClosedIssue(issue) && issue.status !== 'triage'"
                  icon="fa-solid fa-check"
                  variant="success"
                  title="Complete"
                  data-testid="issue-complete-button"
                  @click="transition(issue, 'completed', 'completed')"
                />
                <ActionButton
                  v-if="!isClosedIssue(issue)"
                  icon="fa-solid fa-ban"
                  variant="warning"
                  title="Cancel — close it without doing it"
                  data-testid="issue-cancel-button"
                  @click="openCancel(issue)"
                />
                <ActionButton
                  v-if="isClosedIssue(issue)"
                  icon="fa-solid fa-rotate-left"
                  variant="success"
                  title="Reopen"
                  data-testid="issue-reopen-button"
                  @click="transition(issue, 'open', 'reopened')"
                />
                <ActionButton
                  icon="fa-solid fa-pen-to-square"
                  variant="warning"
                  title="Edit issue"
                  data-testid="issue-edit-button"
                  @click="openEdit(issue)"
                />
                <ActionButton
                  icon="fa-regular fa-trash-can"
                  variant="danger"
                  title="Delete issue"
                  data-testid="issue-delete-button"
                  @click="handleDelete(issue)"
                />
              </span>
            </div>

            <IssueDetailPanel
              v-if="store.expandedId === issue.id"
              :issue="issue"
              :detail="store.detail"
            />
          </template>
        </template>
      </div>
    </div>

    <AddEditIssueModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />

    <CancelIssueModal
      :visible="cancelTarget !== null"
      :issue="cancelTarget"
      @close="cancelTarget = null"
      @cancel="handleCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { Issue, IssueCreate, IssueRankMove, IssueStatus, IssueUpdate } from '@/api/client'
import {
  useIssuesStore,
  isClosedIssue,
  ISSUE_LENSES,
  ISSUE_LENS_LABELS,
  ISSUE_STATUS_LABELS,
  NO_REPO,
  priorityLabel,
  type IssueFilterKey,
  type IssueLens,
} from '@/stores/issues'
import { useIssueInitiativesStore } from '@/stores/issueInitiatives'
import { useNotifications } from '@/composables/useNotifications'
import { formatDate } from '@/composables/formatDate'
import { todayKey } from '@/composables/calendarDay'
import { ApiError } from '@/api/errors'
import ActionButton from '@/components/ActionButton.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import AddEditIssueModal from '@/components/issues/AddEditIssueModal.vue'
import CancelIssueModal from '@/components/issues/CancelIssueModal.vue'
import IssueDetailPanel from '@/components/issues/IssueDetailPanel.vue'
import { ISSUES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = ISSUES_SUBNAV
const store = useIssuesStore()
const initiatives = useIssueInitiativesStore()
const route = useRoute()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<Issue | null>(null)
const cancelTarget = ref<Issue | null>(null)
const searchText = ref(store.search)

const statusOptions = [
  { value: 'unclosed', label: 'Unclosed' },
  { value: 'triage', label: 'Triage' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'canceled', label: 'Canceled' },
  { value: 'all', label: 'Every Status' },
]

const repoOptions = computed(() => {
  const repos = [...store.knownRepos]
  if (store.repoFilter !== 'all' && store.repoFilter !== NO_REPO && !repos.includes(store.repoFilter)) repos.push(store.repoFilter)
  return [
    { value: 'all', label: 'All Repos' },
    { value: NO_REPO, label: 'No Repo' },
    ...repos.map((repo) => ({ value: repo, label: repo })),
  ]
})

const typeOptions = computed(() => [
  { value: 'all', label: 'All Types' },
  ...store.vocabulary.types.map((type) => ({ value: type, label: type })),
])

const labelOptions = computed(() => [
  { value: 'all', label: 'All Labels' },
  ...store.vocabulary.labels.map((label) => ({ value: label.slug, label: `${label.slug} (${label.open_issue_count})` })),
])

const initiativeOptions = computed(() => {
  const names = initiatives.items.map((initiative) => initiative.name)
  if (store.initiativeFilter !== 'all' && !names.includes(store.initiativeFilter)) names.push(store.initiativeFilter)
  return [{ value: 'all', label: 'All Initiatives' }, ...names.map((name) => ({ value: name, label: name }))]
})

const priorityOptions = computed(() => [
  { value: 'all', label: 'Any Priority' },
  ...store.vocabulary.priorities.map((entry) => ({ value: String(entry.value), label: entry.name })),
])

const emptyMessage = computed(() => {
  const active = store.activeFilters
  if (active.length === 0) return 'No open issues.'
  return `No issues match ${active.join(', ')}.`
})

// The star marks a priority the issue did not set: inherited from its parent
// or initiative, or raised by a more urgent issue waiting on it.
function priorityCell(issue: Issue): string {
  const name = priorityLabel(store.vocabulary, issue.effective_priority)
  return issue.effective_priority !== issue.priority ? `${name}*` : name
}

function priorityTitle(issue: Issue): string | undefined {
  if (issue.effective_priority === issue.priority) return undefined
  const own = priorityLabel(store.vocabulary, issue.priority)
  return `Set to ${own}; inherits ${priorityLabel(store.vocabulary, issue.effective_priority)}`
}

/** Why an issue is not simply next: who holds it, what it waits on, and when it may start. */
function stateNotes(issue: Issue): string[] {
  if (isClosedIssue(issue)) return issue.status_reason ? [issue.status_reason] : []
  const notes: string[] = []
  if (issue.status === 'in_progress') {
    notes.push(issue.claimed_by ? `claimed by ${issue.claimed_by}` : 'worked by hand')
  }
  const blockers = issue.depends_on.filter((dependency) => !isClosedIssue(dependency))
  if (blockers.length > 0) notes.push(`waits on ${blockers.map((dependency) => `#${dependency.number}`).join(', ')}`)
  if (issue.deferred_until_date && issue.deferred_until_date > todayKey()) {
    notes.push(`not before ${formatDate(issue.deferred_until_date, 'shortDate')}`)
  }
  if (issue.open_child_count > 0) notes.push(`${issue.open_child_count} open ${issue.open_child_count === 1 ? 'child' : 'children'}`)
  return notes
}

/**
 * The visible row an issue may move past: the unclosed row beside it, when
 * that row sorts at the same effective priority. The rank endpoint answers 409
 * to a move beside any other.
 */
function neighbor(index: number, step: number): Issue | undefined {
  const rows = store.visibleItems
  const self = rows[index]
  const other = rows[index + step]
  if (!self || !other || isClosedIssue(self) || isClosedIssue(other)) return undefined
  return other.effective_priority === self.effective_priority ? other : undefined
}

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`${action} failed: ${detail}`, 'error')
}

const QUERY_FILTERS: IssueFilterKey[] = ['status', 'repo', 'type', 'label', 'initiative', 'priority']

// A link from the initiatives or labels page names the filters it means, so
// they replace whatever this page was last left showing.
function applyRouteQuery() {
  const values: Partial<Record<IssueFilterKey, string>> = {}
  for (const key of QUERY_FILTERS) {
    const value = route.query[key]
    if (typeof value === 'string') values[key] = value
  }
  const lens = route.query.lens
  if (Object.keys(values).length === 0 && typeof lens !== 'string') return
  store.resetFilters()
  store.setFilters(values)
  if (typeof lens === 'string' && (ISSUE_LENSES as string[]).includes(lens)) store.setLens(lens as IssueLens)
  searchText.value = ''
}

onMounted(async () => {
  applyRouteQuery()
  try {
    await Promise.all([store.fetchAll(), store.fetchVocabulary(), initiatives.fetchAll()])
  } catch (e) {
    failure('Loading issues', e)
  }
})

async function applyFilter(key: IssueFilterKey, value: string | number) {
  try {
    await store.setFilter(key, String(value))
  } catch (e) {
    failure('Filtering', e)
  }
}

async function applySearch() {
  try {
    await store.setSearch(searchText.value)
  } catch (e) {
    failure('Searching', e)
  }
}

async function toggle(issue: Issue) {
  try {
    await store.toggleDetail(issue)
  } catch (e) {
    failure(`Loading #${issue.number}`, e)
  }
}

function openCreate() {
  editTarget.value = null
  showModal.value = true
}

function openEdit(issue: Issue) {
  editTarget.value = issue
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

function openCancel(issue: Issue) {
  cancelTarget.value = issue
}

async function handleCreate(data: IssueCreate) {
  try {
    const created = await store.create(data)
    notify(`#${created.number} ${created.title} | added`, 'success')
  } catch (e) {
    failure('Filing', e)
  }
}

async function handleUpdate(issue: Issue, data: IssueUpdate) {
  try {
    await store.update(issue, data)
    notify(`#${issue.number} updated`, 'success')
  } catch (e) {
    failure('Update', e)
  }
}

async function transition(issue: Issue, status: IssueStatus, done: string) {
  try {
    await store.setStatus(issue, status)
    notify(`#${issue.number} ${done}`, 'success')
  } catch (e) {
    failure(`#${issue.number}`, e)
  }
}

async function handleCancel(closure: Pick<IssueUpdate, 'status_reason' | 'duplicate_of'>) {
  const issue = cancelTarget.value
  cancelTarget.value = null
  if (!issue) return
  try {
    await store.setStatus(issue, 'canceled', closure)
    notify(`#${issue.number} canceled`, 'success')
  } catch (e) {
    failure('Cancel', e)
  }
}

async function release(issue: Issue) {
  try {
    await store.release(issue)
    notify(`#${issue.number} released`, 'success')
  } catch (e) {
    failure('Release', e)
  }
}

async function moveIssue(issue: Issue, placement: IssueRankMove) {
  try {
    await store.move(issue, placement)
  } catch (e) {
    failure('Move', e)
  }
}

async function handleDelete(issue: Issue) {
  try {
    await store.remove(issue)
    notify(`#${issue.number} ${issue.title} | deleted`, 'success')
  } catch (e) {
    failure('Delete', e)
  }
}
</script>
