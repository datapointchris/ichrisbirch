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
          class="grid__item"
          :class="{ 'grid__item--highlighted': event.attending }"
        >
          <h2>{{ event.name }}</h2>
          <ul class="event">
            <li class="event__item">{{ formatEventDate(event.date) }} | {{ event.venue }}</li>
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
              class="button"
              @click="handleToggleAttending(event.id)"
            >
              <span class="button__text">Attend Event</span>
            </button>
            <button
              v-else
              class="button button--pressed"
              @click="handleToggleAttending(event.id)"
            >
              Attending
            </button>
            <button
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
      <h2>Add New Event</h2>
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
          <label for="date">Date and Time:</label>
          <input
            id="date"
            v-model="form.date"
            type="datetime-local"
            class="textbox"
            name="date"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="url">URL:</label>
          <input
            id="url"
            v-model="form.url"
            type="text"
            class="textbox"
            name="url"
          />
        </div>
        <div class="add-item-form__item">
          <label for="venue">Venue:</label>
          <input
            id="venue"
            v-model="form.venue"
            type="text"
            class="textbox"
            name="venue"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="cost">Cost:</label>
          <input
            id="cost"
            v-model="form.cost"
            type="number"
            class="textbox"
            name="cost"
            step="any"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="attending">Attending:</label>
          <input
            id="attending"
            v-model="form.attending"
            type="checkbox"
            class="textbox"
            name="attending"
          />
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
            <span class="button__text">Add Event</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useEventsStore } from '@/stores/events'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'

const store = useEventsStore()
const { show: notify } = useNotifications()

const form = reactive({
  name: '',
  date: '',
  url: '',
  venue: '',
  cost: 0,
  attending: false,
  notes: '',
})

onMounted(() => {
  store.fetchAll()
})

function formatEventDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: '2-digit',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`
}

async function handleAdd() {
  if (!form.name.trim() || !form.date || !form.venue.trim()) return
  try {
    await store.create({
      name: form.name.trim(),
      date: form.date,
      venue: form.venue.trim(),
      url: form.url.trim() || undefined,
      cost: Number(form.cost),
      attending: form.attending,
      notes: form.notes.trim() || undefined,
    })
    notify('Event added', 'success')
    form.name = ''
    form.date = ''
    form.url = ''
    form.venue = ''
    form.cost = 0
    form.attending = false
    form.notes = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add event: ${detail}`, 'error')
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
