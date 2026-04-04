<template>
  <div>
    <div class="add-item-wrapper">
      <button
        data-testid="autotask-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add AutoTask</span>
      </button>
    </div>

    <div class="grid grid--two-columns">
      <div
        v-if="store.loading"
        class="grid__item"
      >
        <h2>Loading...</h2>
      </div>
      <div
        v-else-if="store.sortedAutoTasks.length === 0"
        class="grid__item"
      >
        <h2>No AutoTasks</h2>
      </div>
      <template v-else>
        <div
          v-for="autotask in store.sortedAutoTasks"
          :key="autotask.id"
          data-testid="autotask-item"
          class="grid__item"
        >
          <h2>{{ autotask.name }}</h2>
          <div class="item-details">
            <div class="item-details__item">
              <strong>Category</strong>
              <span class="item-details__item-content">{{ autotask.category }}</span>
            </div>
            <div class="item-details__item">
              <strong>Priority</strong>
              <span class="item-details__item-content">{{ autotask.priority }}</span>
            </div>
            <div class="item-details__item">
              <strong>Frequency</strong>
              <span class="item-details__item-content">{{ autotask.frequency }}</span>
            </div>
            <div class="item-details__item">
              <strong>Run Count</strong>
              <span class="item-details__item-content">{{ autotask.run_count }}</span>
            </div>
            <div class="item-details__item">
              <strong>First Run Date</strong>
              <span class="item-details__item-content">{{ formatDate(autotask.first_run_date, 'dateTime') }}</span>
            </div>
            <div class="item-details__item">
              <strong>Last Run Date</strong>
              <span class="item-details__item-content">{{ formatDate(autotask.last_run_date, 'dateTime') }}</span>
            </div>
            <div
              v-if="autotask.notes"
              class="item-details__item item-details__item--full-width"
            >
              <strong>Notes</strong>
              <span class="item-details__item-content">{{ autotask.notes }}</span>
            </div>
            <div class="item-details__buttons">
              <button
                data-testid="autotask-run-button"
                class="button"
                @click="handleRun(autotask.id, autotask.name)"
              >
                <span class="button__text">Run Autotask Now</span>
              </button>
              <button
                data-testid="autotask-edit-button"
                class="button"
                @click="openEdit(autotask)"
              >
                <span class="button__text">Edit</span>
              </button>
              <button
                data-testid="autotask-delete-button"
                class="button button--danger"
                @click="handleDelete(autotask.id)"
              >
                <span class="button__text button__text--danger">Delete Autotask</span>
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <AddEditAutoTaskModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAutoTasksStore } from '@/stores/autotasks'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { AutoTask, AutoTaskCreate, AutoTaskUpdate } from '@/api/client'
import AddEditAutoTaskModal from '@/components/autotasks/AddEditAutoTaskModal.vue'
import { formatDate } from '@/composables/formatDate'

const store = useAutoTasksStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<AutoTask | null>(null)

onMounted(() => {
  store.fetchAll()
})

function openEdit(autotask: AutoTask) {
  editTarget.value = autotask
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: AutoTaskCreate) {
  try {
    await store.create(data)
    notify(`${data.name} added and ran`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add autotask: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: AutoTaskUpdate) {
  const name = store.autotasks.find((a) => a.id === id)?.name ?? 'AutoTask'
  try {
    await store.update(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update autotask: ${detail}`, 'error')
  }
}

async function handleRun(id: number, name: string) {
  try {
    await store.run(id)
    notify(`Ran ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to run autotask: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  const name = store.autotasks.find((a) => a.id === id)?.name ?? 'AutoTask'
  try {
    await store.remove(id)
    notify(`${name} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete autotask: ${detail}`, 'error')
  }
}
</script>
