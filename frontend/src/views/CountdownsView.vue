<template>
  <div>
    <div class="grid grid--one-column">
      <div
        v-if="store.loading"
        class="grid__item"
      >
        <h2>Loading...</h2>
      </div>
      <div
        v-else-if="store.sortedCountdowns.length === 0"
        class="grid__item"
      >
        <h2>No Countdowns</h2>
      </div>
      <template v-else>
        <div
          v-for="countdown in store.sortedCountdowns"
          :key="countdown.id"
          class="grid__item"
        >
          <h2>{{ countdown.name }}</h2>
          <h2
            class="daysleft"
            :class="urgencyClass(countdown.due_date)"
          >
            {{ daysLeftText(countdown.due_date) }}
          </h2>
          {{ formatDate(countdown.due_date) }}
          <br />
          {{ countdown.notes }}
          <br /><br />
          <button
            class="button button--danger"
            @click="handleDelete(countdown.id)"
          >
            <span class="button__text button__text--danger">Delete Countdown</span>
          </button>
        </div>
      </template>
    </div>

    <div class="add-item-wrapper">
      <h2>Add New Countdown:</h2>
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
            size="30"
            class="textbox"
            name="name"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="due_date">Due Date:</label>
          <DatePicker
            :model-value="form.due_date"
            @update:model-value="form.due_date = $event"
          />
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="notes">Notes:</label>
          <input
            id="notes"
            v-model="form.notes"
            type="text"
            size="40"
            class="textbox"
            name="notes"
          />
        </div>
        <div class="add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Countdown</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useCountdownsStore } from '@/stores/countdowns'
import { useNotifications } from '@/composables/useNotifications'
import { computeDaysLeft, formatDate } from '@/composables/useDaysLeft'
import { ApiError } from '@/api/errors'
import DatePicker from '@/components/DatePicker.vue'

const store = useCountdownsStore()
const { show: notify } = useNotifications()

const form = reactive({
  name: '',
  due_date: '',
  notes: '',
})

onMounted(() => {
  store.fetchAll()
})

function daysLeftText(dueDate: string): string {
  return computeDaysLeft(dueDate).text
}

function urgencyClass(dueDate: string): string {
  const { urgency } = computeDaysLeft(dueDate)
  if (urgency === 'past') return 'past'
  if (urgency === 'two-weeks') return 'two-weeks-left'
  if (urgency === 'month') return 'month-left'
  return ''
}

async function handleAdd() {
  if (!form.name.trim() || !form.due_date) return
  try {
    await store.create({
      name: form.name.trim(),
      due_date: form.due_date,
      notes: form.notes.trim() || undefined,
    })
    notify('Countdown added', 'success')
    form.name = ''
    form.due_date = ''
    form.notes = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add countdown: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    notify('Countdown deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete countdown: ${detail}`, 'error')
  }
}
</script>
