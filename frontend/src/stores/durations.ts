import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Duration, DurationCreate, DurationUpdate, DurationNote, DurationNoteCreate, DurationNoteUpdate } from '@/api/client'

const logger = createLogger('DurationsStore')

export const useDurationsStore = defineStore('durations', () => {
  const durations = ref<Duration[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedDurations = computed(() => [...durations.value].sort((a, b) => a.start_date.localeCompare(b.start_date)))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Duration[]>('/durations/')
      durations.value = response.data
      logger.info('durations_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('durations_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: DurationCreate) {
    error.value = null
    try {
      const response = await api.post<Duration>('/durations/', input)
      durations.value.push(response.data)
      logger.info('duration_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: DurationUpdate) {
    error.value = null
    try {
      const response = await api.patch<Duration>(`/durations/${id}/`, input)
      const index = durations.value.findIndex((d) => d.id === id)
      if (index !== -1) {
        durations.value[index] = response.data
      }
      logger.info('duration_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/durations/${id}/`)
      durations.value = durations.value.filter((d) => d.id !== id)
      logger.info('duration_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function addNote(durationId: number, input: DurationNoteCreate) {
    error.value = null
    try {
      const response = await api.post<DurationNote>(`/durations/${durationId}/notes/`, input)
      const duration = durations.value.find((d) => d.id === durationId)
      if (duration) {
        duration.duration_notes.push(response.data)
        duration.duration_notes.sort((a, b) => a.date.localeCompare(b.date))
      }
      logger.info('duration_note_created', { duration_id: durationId, note_id: response.data.id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_note_create_failed', { duration_id: durationId, detail: apiError.detail })
      throw apiError
    }
  }

  async function updateNote(durationId: number, noteId: number, input: DurationNoteUpdate) {
    error.value = null
    try {
      const response = await api.patch<DurationNote>(`/durations/${durationId}/notes/${noteId}/`, input)
      const duration = durations.value.find((d) => d.id === durationId)
      if (duration) {
        const noteIndex = duration.duration_notes.findIndex((n) => n.id === noteId)
        if (noteIndex !== -1) {
          duration.duration_notes[noteIndex] = response.data
          duration.duration_notes.sort((a, b) => a.date.localeCompare(b.date))
        }
      }
      logger.info('duration_note_updated', { duration_id: durationId, note_id: noteId })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_note_update_failed', { duration_id: durationId, note_id: noteId, detail: apiError.detail })
      throw apiError
    }
  }

  async function removeNote(durationId: number, noteId: number) {
    error.value = null
    try {
      await api.delete(`/durations/${durationId}/notes/${noteId}/`)
      const duration = durations.value.find((d) => d.id === durationId)
      if (duration) {
        duration.duration_notes = duration.duration_notes.filter((n) => n.id !== noteId)
      }
      logger.info('duration_note_deleted', { duration_id: durationId, note_id: noteId })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('duration_note_delete_failed', { duration_id: durationId, note_id: noteId, detail: apiError.detail })
      throw apiError
    }
  }

  return {
    durations,
    loading,
    error,
    sortedDurations,
    clearError,
    fetchAll,
    create,
    update,
    remove,
    addNote,
    updateNote,
    removeNote,
  }
})
