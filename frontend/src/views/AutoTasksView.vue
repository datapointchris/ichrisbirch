<template>
  <div>
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
              <span class="item-details__item-content">{{ formatDate(autotask.first_run_date) }}</span>
            </div>
            <div class="item-details__item">
              <strong>Last Run Date</strong>
              <span class="item-details__item-content">{{ formatDate(autotask.last_run_date) }}</span>
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
                class="button"
                @click="handleRun(autotask.id, autotask.name)"
              >
                <span class="button__text">Run Autotask Now</span>
              </button>
              <button
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

    <div class="add-item-wrapper">
      <h2>Add New AutoTask</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleAdd"
      >
        <div class="add-item-form__item">
          <label for="name">Name:</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            class="textbox"
            name="name"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="priority">Priority:</label>
          <input
            id="priority"
            v-model="form.priority"
            type="number"
            min="1"
            class="textbox"
            name="priority"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="category">Category:</label>
          <select
            id="category"
            v-model="form.category"
            class="textbox"
            name="category"
          >
            <option
              v-for="cat in TASK_CATEGORIES"
              :key="cat"
              :value="cat"
            >
              {{ cat }}
            </option>
          </select>
        </div>
        <div class="add-item-form__item">
          <label for="frequency">Task Frequency:</label>
          <select
            id="frequency"
            v-model="form.frequency"
            class="textbox"
            name="frequency"
          >
            <option
              v-for="freq in AUTOTASK_FREQUENCIES"
              :key="freq"
              :value="freq"
            >
              {{ freq }}
            </option>
          </select>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="notes">Notes:</label>
          <textarea
            id="notes"
            v-model="form.notes"
            rows="3"
            class="textbox"
            name="notes"
          ></textarea>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add New Autotask</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useAutoTasksStore, TASK_CATEGORIES, AUTOTASK_FREQUENCIES } from '@/stores/autotasks'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'

const store = useAutoTasksStore()
const { show: notify } = useNotifications()

const form = reactive({
  name: '',
  priority: 1,
  category: 'Chore' as (typeof TASK_CATEGORIES)[number],
  frequency: 'Monthly' as (typeof AUTOTASK_FREQUENCIES)[number],
  notes: '',
})

onMounted(() => {
  store.fetchAll()
})

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

async function handleAdd() {
  if (!form.name.trim()) return
  try {
    await store.create({
      name: form.name.trim(),
      priority: Number(form.priority),
      category: form.category,
      frequency: form.frequency,
      notes: form.notes.trim() || undefined,
    })
    notify('AutoTask added and ran', 'success')
    form.name = ''
    form.priority = 1
    form.category = 'Chore'
    form.frequency = 'Monthly'
    form.notes = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add autotask: ${detail}`, 'error')
  }
}

async function handleRun(id: number, name: string) {
  try {
    await store.run(id)
    notify(`Ran autotask: ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to run autotask: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    notify('AutoTask deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete autotask: ${detail}`, 'error')
  }
}
</script>
