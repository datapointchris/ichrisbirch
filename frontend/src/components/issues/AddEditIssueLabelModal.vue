<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="editData ? groupInput : slugInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? `Edit ${editData.slug}` : 'Add a Label' }}</h2>

        <div
          v-if="!editData"
          class="add-edit-modal__form-item"
        >
          <label for="issue-label-slug">Label</label>
          <input
            id="issue-label-slug"
            ref="slugInput"
            v-model="form.slug"
            data-testid="issue-label-slug-input"
            type="text"
            class="textbox"
            :class="{ 'textbox--error': errors.slug }"
            placeholder="area-cli"
            required
            @input="clearError('slug')"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="issue-label-group">Group</label>
          <input
            id="issue-label-group"
            ref="groupInput"
            v-model="form.group"
            data-testid="issue-label-group-input"
            type="text"
            class="textbox"
            :class="{ 'textbox--error': errors.group }"
            :placeholder="groupHint"
            @input="clearError('group')"
          />
          <span class="issue-modal__note">An issue takes one label from a group. Blank leaves the label ungrouped.</span>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="issue-label-description">Description</label>
          <input
            id="issue-label-description"
            v-model="form.description"
            data-testid="issue-label-description-input"
            type="text"
            class="textbox"
          />
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="issue-label-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Label</span>
          </button>
          <button
            type="button"
            data-testid="issue-label-cancel-button"
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
import type { IssueLabel, IssueLabelCreate, IssueLabelUpdate } from '@/api/client'
import { useIssueLabelsStore } from '@/stores/issueLabels'
import { useFieldErrors } from '@/composables/useFieldErrors'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  editData?: IssueLabel | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: IssueLabelCreate]
  update: [slug: string, data: IssueLabelUpdate]
}>()

const labels = useIssueLabelsStore()
const { errors, validate, clearError, clearAll } = useFieldErrors()
const slugInput = ref<HTMLInputElement | null>(null)
const groupInput = ref<HTMLInputElement | null>(null)

// The API's slug shape: lowercase words joined by single hyphens.
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/

const groupHint = computed(() => (labels.groups.length > 0 ? labels.groups.join(', ') : 'area'))

function createEmptyForm() {
  return { slug: '', group: '', description: '' }
}

const form = reactive(createEmptyForm())

watch(
  () => props.visible,
  (val) => {
    clearAll()
    if (val && props.editData) {
      Object.assign(form, {
        slug: props.editData.slug,
        group: props.editData.group_slug ?? '',
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

function slugFault(value: string, what: string): string | null {
  return value && !SLUG.test(value) ? `${what} "${value}" must be lowercase words joined by hyphens` : null
}

function handleSubmit(handleSuccess: () => void) {
  const slug = form.slug.trim()
  const group = form.group.trim()
  const description = form.description.trim()
  const valid = validate({
    slug: props.editData ? null : (slugFault(slug, 'Label') ?? (slug ? null : 'A label needs a name')),
    group: slugFault(group, 'Group'),
  })
  if (!valid) return
  if (props.editData) {
    emit('update', props.editData.slug, { group_slug: group || null, description: description || null })
  } else {
    const payload: IssueLabelCreate = { slug }
    if (group) payload.group_slug = group
    if (description) payload.description = description
    emit('create', payload)
  }
  handleSuccess()
}
</script>
