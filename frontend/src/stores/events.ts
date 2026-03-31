import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Event, EventCreate, EventUpdate } from '@/api/client'

const logger = createLogger('EventsStore')

export const useEventsStore = defineStore('events', () => {
  const events = ref<Event[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedEvents = computed(() => {
    const now = new Date().toISOString()
    return [...events.value].sort((a, b) => {
      const aPast = a.date < now
      const bPast = b.date < now
      if (aPast !== bPast) return aPast ? 1 : -1
      return a.date.localeCompare(b.date)
    })
  })

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Event[]>('/events/')
      events.value = response.data
      logger.info('events_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('events_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: EventCreate) {
    error.value = null
    try {
      const response = await api.post<Event>('/events/', input)
      events.value.push(response.data)
      logger.info('event_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('event_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: EventUpdate) {
    error.value = null
    try {
      const response = await api.patch<Event>(`/events/${id}/`, input)
      const index = events.value.findIndex((e) => e.id === id)
      if (index !== -1) {
        events.value[index] = response.data
      }
      logger.info('event_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('event_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/events/${id}/`)
      events.value = events.value.filter((e) => e.id !== id)
      logger.info('event_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('event_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function toggleAttending(id: number) {
    error.value = null
    try {
      const event = events.value.find((e) => e.id === id)
      if (!event) return
      const response = await api.patch<Event>(`/events/${id}/`, { attending: !event.attending })
      const index = events.value.findIndex((e) => e.id === id)
      if (index !== -1) {
        events.value[index] = response.data
      }
      logger.info('event_attending_toggled', { id, attending: response.data.attending })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('event_attending_toggle_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    events,
    loading,
    error,
    sortedEvents,
    clearError,
    fetchAll,
    create,
    update,
    remove,
    toggleAttending,
  }
})
