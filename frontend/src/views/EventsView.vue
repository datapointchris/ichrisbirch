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
        v-else-if="store.sortedEvents.length === 0"
        class="grid__item"
      >
        <h2>No Events</h2>
      </div>
      <template v-else>
        <div
          v-for="event in store.sortedEvents"
          :key="event.id"
          data-testid="event-item"
          class="grid__item"
          :class="{ 'grid__item--highlighted': event.attending }"
        >
          <h2>{{ event.name }}</h2>
          <ul class="event">
            <li class="event__item">{{ formatDate(event.date, 'weekdayDateTime') }} | {{ event.venue }}</li>
            <li class="event__item">
              <a
                v-if="event.url"
                :href="event.url"
                target="_blank"
                >Event URL</a
              >
              <span v-if="event.url"> | </span>
              {{ formatCost(event.cost) }} | Attending: {{ event.attending ? 'YES' : 'No' }}
            </li>
            <li
              v-if="event.notes"
              class="event__item"
            >
              Notes: {{ event.notes }}
            </li>
          </ul>
          <div class="event__buttons">
            <button
              v-if="!event.attending"
              data-testid="event-attend-button"
              class="button"
              @click="handleToggleAttending(event.id)"
            >
              <span class="button__text">Attend Event</span>
            </button>
            <button
              v-else
              data-testid="event-attend-button"
              class="button button--pressed"
              @click="handleToggleAttending(event.id)"
            >
              Attending
            </button>
            <button
              data-testid="event-edit-button"
              class="button"
              @click="openEdit(event)"
            >
              <span class="button__text">Edit</span>
            </button>
            <button
              data-testid="event-delete-button"
              class="button button--danger"
              @click="handleDelete(event.id)"
            >
              <span class="button__text button__text--danger">Delete Event</span>
            </button>
          </div>
        </div>
      </template>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="event-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Event</span>
      </button>
    </div>

    <AddEditEventModal
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
import { useEventsStore } from '@/stores/events'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Event, EventCreate, EventUpdate } from '@/api/client'
import AddEditEventModal from '@/components/events/AddEditEventModal.vue'
import { formatDate } from '@/composables/formatDate'

const store = useEventsStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<Event | null>(null)

onMounted(() => {
  store.fetchAll()
})

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`
}

function openEdit(event: Event) {
  editTarget.value = event
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: EventCreate) {
  try {
    await store.create(data)
    notify('Event added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add event: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: EventUpdate) {
  try {
    await store.update(id, data)
    notify('Event updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update event: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    notify('Event deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete event: ${detail}`, 'error')
  }
}

async function handleToggleAttending(id: number) {
  try {
    const updated = await store.toggleAttending(id)
    if (updated) {
      notify(updated.attending ? 'Attending event' : 'No longer attending', 'success')
    }
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update attendance: ${detail}`, 'error')
  }
}
</script>
