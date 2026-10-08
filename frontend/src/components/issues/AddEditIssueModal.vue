<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="titleInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? `Edit #${editData.number}` : 'File an Issue' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="issue-title">Title</label>
          <input
            id="issue-title"
            ref="titleInput"
            v-model="form.title"
            data-testid="issue-title-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label>Type</label>
            <NeuSelect
              :model-value="form.type"
              :options="typeOptions"
              data-testid="issue-type-input"
              @update:model-value="form.type = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label>Priority</label>
            <NeuSelect
              :model-value="form.priority"
              :options="priorityOptions"
              data-testid="issue-priority-input"
              @update:model-value="form.priority = $event"
            />
          </div>
          <div
            v-if="!editData"
            class="add-edit-modal__form-item"
          >
            <label>Starts as</label>
            <NeuSelect
              :model-value="form.status"
              :options="createStatusOptions"
              data-testid="issue-status-input"
              @update:model-value="form.status = $event"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="issue-repo">Repo</label>
            <input
              id="issue-repo"
              v-model="form.repo"
              data-testid="issue-repo-input"
              type="text"
              class="textbox"
              placeholder="Blank for work on no repo"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label>Initiative</label>
            <NeuSelect
              :model-value="form.initiative"
              :options="initiativeOptions"
              data-testid="issue-initiative-input"
              @update:model-value="form.initiative = $event"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label>Labels</label>
          <div class="issue-chips">
            <div
              v-for="group in labelGroups"
              :key="group.name"
              class="issue-chips__group"
            >
              <span class="issue-chips__group-name">{{ group.name }}</span>
              <button
                v-for="chip in group.chips"
                :key="chip.slug"
                type="button"
                class="issue-chips__chip"
                :class="{
                  'issue-chips__chip--on': form.labels.includes(chip.slug),
                  'issue-chips__chip--undefined': chip.orphan,
                }"
                :data-testid="`issue-label-${chip.slug}`"
                :title="chip.orphan ? 'Not in the vocabulary — click to remove it' : (chip.description ?? undefined)"
                @click="toggleLabel(chip.slug, chip.group)"
              >
                {{ chip.slug }}
              </button>
            </div>
            <span
              v-if="labelGroups.length === 0"
              class="issues__empty"
              >No labels defined.</span
            >
          </div>
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="issue-parent">Parent issue</label>
            <input
              id="issue-parent"
              v-model="form.parent"
              data-testid="issue-parent-input"
              type="text"
              class="textbox"
              :class="{ 'textbox--error': errors.parent }"
              placeholder="#812"
              @input="clearError('parent')"
            />
          </div>
          <div
            v-if="!editData"
            class="add-edit-modal__form-item"
          >
            <label for="issue-depends-on">Waits on</label>
            <input
              id="issue-depends-on"
              v-model="form.depends_on"
              data-testid="issue-depends-on-input"
              type="text"
              class="textbox"
              :class="{ 'textbox--error': errors.depends_on }"
              placeholder="#812, #815"
              @input="clearError('depends_on')"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="issue-deferred-until">Not before</label>
            <DatePicker
              id="issue-deferred-until"
              data-testid="issue-deferred-until-input"
              :model-value="form.deferred_until_date"
              @update:model-value="form.deferred_until_date = $event"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="issue-description">Description</label>
          <textarea
            id="issue-description"
            v-model="form.description"
            data-testid="issue-description-input"
            rows="4"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="issue-acceptance">Done when</label>
          <textarea
            id="issue-acceptance"
            v-model="form.acceptance"
            data-testid="issue-acceptance-input"
            rows="3"
            class="textbox"
            placeholder="What has to be true to close it"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="issue-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'File' }} Issue</span>
          </button>
          <button
            type="button"
            data-testid="issue-cancel-button"
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
import type { Issue, IssueCreate, IssueUpdate } from '@/api/client'
import { useIssuesStore } from '@/stores/issues'
import { useIssueInitiativesStore } from '@/stores/issueInitiatives'
import { useFieldErrors } from '@/composables/useFieldErrors'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import { parseIssueNumber, parseIssueNumbers } from '@/components/issues/issueNumbers'

const props = defineProps<{
  visible: boolean
  editData?: Issue | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: IssueCreate]
  update: [issue: Issue, data: IssueUpdate]
}>()

const store = useIssuesStore()
const initiatives = useIssueInitiativesStore()
const { errors, validate, clearError, clearAll } = useFieldErrors()
const titleInput = ref<HTMLInputElement | null>(null)

const UNGROUPED = 'ungrouped'

const typeOptions = computed(() => store.vocabulary.types.map((type) => ({ value: type, label: type })))

const priorityOptions = computed(() => store.vocabulary.priorities.map((entry) => ({ value: entry.value, label: entry.name })))

const createStatusOptions: { value: 'open' | 'triage'; label: string }[] = [
  { value: 'open', label: 'Open — ready to work' },
  { value: 'triage', label: 'Triage — needs a look first' },
]

// A finished initiative takes no new issues, so it is offered only when the
// issue being edited already belongs to it.
const initiativeOptions = computed(() => {
  const names = initiatives.items.filter((initiative) => initiative.status === 'active').map((initiative) => initiative.name)
  const current = props.editData?.initiative?.name
  if (current && !names.includes(current)) names.push(current)
  return [{ value: '', label: '— none —' }, ...names.map((name) => ({ value: name, label: name }))]
})

function createEmptyForm() {
  return {
    title: '',
    type: 'task',
    priority: 0,
    status: 'open' as 'open' | 'triage',
    repo: '',
    initiative: '',
    labels: [] as string[],
    parent: '',
    depends_on: '',
    deferred_until_date: '',
    description: '',
    acceptance: '',
  }
}

const form = reactive(createEmptyForm())

/**
 * Chips grouped the way the vocabulary groups them, plus any label the issue
 * carries that the vocabulary does not define. The API refuses an undefined
 * label and the whole set is resent, so a label with no chip would make the
 * issue unsavable; it renders marked, and clicking it off is the way out.
 */
const labelGroups = computed(() => {
  const groups = new Map<string, { slug: string; group: string | null; description: string | null; orphan: boolean }[]>()
  for (const label of store.vocabulary.labels) {
    const name = label.group_slug ?? UNGROUPED
    const chips = groups.get(name) ?? []
    chips.push({ slug: label.slug, group: label.group_slug, description: label.description, orphan: false })
    groups.set(name, chips)
  }
  const known = new Set(store.vocabulary.labels.map((label) => label.slug))
  const orphans = form.labels.filter((slug) => !known.has(slug))
  if (orphans.length > 0) {
    groups.set(
      'undefined',
      orphans.map((slug) => ({ slug, group: null, description: null, orphan: true }))
    )
  }
  return [...groups.entries()].map(([name, chips]) => ({ name, chips }))
})

// A group's labels exclude each other, so choosing one sets the rest down
// rather than leaving a pair the API would refuse.
function toggleLabel(slug: string, group: string | null) {
  if (form.labels.includes(slug)) {
    form.labels = form.labels.filter((value) => value !== slug)
    return
  }
  const siblings = group
    ? new Set(store.vocabulary.labels.filter((label) => label.group_slug === group).map((label) => label.slug))
    : new Set()
  form.labels = [...form.labels.filter((value) => !siblings.has(value)), slug]
}

watch(
  () => props.visible,
  (val) => {
    clearAll()
    if (val && props.editData) {
      const issue = props.editData
      Object.assign(form, createEmptyForm(), {
        title: issue.title,
        type: issue.type,
        priority: issue.priority,
        repo: issue.repo ?? '',
        initiative: issue.initiative?.name ?? '',
        labels: [...issue.labels],
        parent: issue.parent ? `#${issue.parent.number}` : '',
        deferred_until_date: issue.deferred_until_date ?? '',
        description: issue.description ?? '',
        acceptance: issue.acceptance ?? '',
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

function buildCreate(parent: number | null, dependsOn: number[]): IssueCreate {
  const payload: IssueCreate = { title: form.title.trim(), type: form.type, priority: form.priority, status: form.status }
  if (form.repo.trim()) payload.repo = form.repo.trim()
  if (form.initiative) payload.initiative = form.initiative
  if (form.labels.length > 0) payload.labels = [...form.labels]
  if (parent !== null) payload.parent = parent
  if (dependsOn.length > 0) payload.depends_on = dependsOn
  if (form.deferred_until_date) payload.deferred_until_date = form.deferred_until_date
  if (form.description.trim()) payload.description = form.description.trim()
  if (form.acceptance.trim()) payload.acceptance = form.acceptance.trim()
  return payload
}

// An edit sends every field, with an explicit null to clear one.
function buildUpdate(parent: number | null): IssueUpdate {
  return {
    title: form.title.trim(),
    type: form.type,
    priority: form.priority,
    repo: form.repo.trim() || null,
    initiative: form.initiative || null,
    labels: [...form.labels],
    parent,
    deferred_until_date: form.deferred_until_date || null,
    description: form.description.trim() || null,
    acceptance: form.acceptance.trim() || null,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.title.trim()) return
  const parent = form.parent.trim() ? parseIssueNumber(form.parent) : null
  const dependsOn = props.editData ? [] : parseIssueNumbers(form.depends_on)
  const valid = validate({
    parent: form.parent.trim() && parent === null ? `"${form.parent.trim()}" is not an issue number` : null,
    depends_on: dependsOn === null ? `"${form.depends_on.trim()}" holds something that is not an issue number` : null,
  })
  if (!valid) return
  if (props.editData) {
    emit('update', props.editData, buildUpdate(parent))
  } else {
    emit('create', buildCreate(parent, dependsOn ?? []))
  }
  handleSuccess()
}
</script>
