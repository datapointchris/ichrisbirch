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
          data-testid="countdown-item"
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
            data-testid="countdown-edit-button"
            class="button"
            @click="openEdit(countdown)"
          >
            <span class="button__text">Edit</span>
          </button>
          <button
            data-testid="countdown-delete-button"
            class="button button--danger"
            @click="handleDelete(countdown.id)"
          >
            <span class="button__text button__text--danger">Delete Countdown</span>
          </button>
        </div>
      </template>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="countdown-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Countdown</span>
      </button>
    </div>

    <AddEditCountdownModal
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
import { useCountdownsStore } from '@/stores/countdowns'
import { useNotifications } from '@/composables/useNotifications'
import { computeDaysLeft, formatDate } from '@/composables/useDaysLeft'
import { ApiError } from '@/api/errors'
import type { Countdown, CountdownCreate, CountdownUpdate } from '@/api/client'
import AddEditCountdownModal from '@/components/countdowns/AddEditCountdownModal.vue'

const store = useCountdownsStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<{ id: number; name: string; due_date: string; notes?: string } | null>(null)

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

function openEdit(countdown: Countdown) {
  editTarget.value = {
    id: countdown.id,
    name: countdown.name,
    due_date: countdown.due_date,
    notes: countdown.notes,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: CountdownCreate) {
  try {
    await store.create(data)
    notify('Countdown added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add countdown: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: CountdownUpdate) {
  try {
    await store.update(id, data)
    notify('Countdown updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update countdown: ${detail}`, 'error')
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
