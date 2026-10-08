<template>
  <div>
    <AppSubnav :links="subnavLinks">
      <button
        data-testid="issue-label-add-button"
        class="button"
        @click="openCreate"
      >
        <span class="button__text">Add Label</span>
      </button>
    </AppSubnav>

    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="issue-labels__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div
            class="issue-labels__header"
            data-testid="issue-labels-header"
          >
            <span>Label</span>
            <span>Group</span>
            <span>Open</span>
            <span>Description</span>
            <span>Actions</span>
          </div>

          <div
            v-if="store.items.length === 0"
            class="issue-labels__empty"
            data-testid="issue-label-empty"
          >
            No labels yet. Add one!
          </div>

          <div
            v-for="label in store.items"
            :key="label.slug"
            data-testid="issue-label-item"
            class="issue-labels__row"
          >
            <span>
              <RouterLink
                :to="{ path: '/issues', query: { label: label.slug } }"
                class="issue-labels__link"
                data-testid="issue-label-issues-link"
                >{{ label.slug }}</RouterLink
              >
            </span>
            <span>{{ label.group_slug ?? '—' }}</span>
            <span>{{ label.open_issue_count }}</span>
            <span :title="label.description ?? undefined">{{ label.description ?? '' }}</span>
            <span class="issue-labels__actions">
              <ActionButton
                icon="fa-solid fa-pen-to-square"
                variant="warning"
                title="Edit label"
                data-testid="issue-label-edit-button"
                @click="openEdit(label)"
              />
              <ActionButton
                icon="fa-regular fa-trash-can"
                variant="danger"
                title="Delete label — it comes off every issue carrying it"
                data-testid="issue-label-delete-button"
                @click="handleDelete(label)"
              />
            </span>
          </div>
        </template>
      </div>
    </div>

    <AddEditIssueLabelModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { IssueLabel, IssueLabelCreate, IssueLabelUpdate } from '@/api/client'
import { useIssueLabelsStore } from '@/stores/issueLabels'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import ActionButton from '@/components/ActionButton.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import AddEditIssueLabelModal from '@/components/issues/AddEditIssueLabelModal.vue'
import { ISSUES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = ISSUES_SUBNAV
const store = useIssueLabelsStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<IssueLabel | null>(null)

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`${action} failed: ${detail}`, 'error')
}

onMounted(async () => {
  try {
    await store.fetchAll()
  } catch (e) {
    failure('Loading labels', e)
  }
})

function openCreate() {
  editTarget.value = null
  showModal.value = true
}

function openEdit(label: IssueLabel) {
  editTarget.value = label
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: IssueLabelCreate) {
  try {
    await store.create(data)
    notify(`${data.slug} | added`, 'success')
  } catch (e) {
    failure('Adding the label', e)
  }
}

async function handleUpdate(slug: string, data: IssueLabelUpdate) {
  try {
    await store.update(slug, data)
    notify(`${slug} updated`, 'success')
  } catch (e) {
    failure('Update', e)
  }
}

async function handleDelete(label: IssueLabel) {
  try {
    await store.remove(label.slug)
    notify(`${label.slug} | deleted`, 'success')
  } catch (e) {
    failure('Delete', e)
  }
}
</script>
