import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Countdown, CountdownCreate, CountdownUpdate } from '@/api/client'

const logger = createLogger('CountdownsStore')

export const useCountdownsStore = defineStore('countdowns', () => {
  const countdowns = ref<Countdown[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedCountdowns = computed(() => [...countdowns.value].sort((a, b) => a.due_date.localeCompare(b.due_date)))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Countdown[]>('/countdowns/')
      countdowns.value = response.data
      logger.info('countdowns_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('countdowns_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: CountdownCreate) {
    error.value = null
    try {
      const response = await api.post<Countdown>('/countdowns/', input)
      countdowns.value.push(response.data)
      logger.info('countdown_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('countdown_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: CountdownUpdate) {
    error.value = null
    try {
      const response = await api.patch<Countdown>(`/countdowns/${id}/`, input)
      const index = countdowns.value.findIndex((c) => c.id === id)
      if (index !== -1) {
        countdowns.value[index] = response.data
      }
      logger.info('countdown_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('countdown_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/countdowns/${id}/`)
      countdowns.value = countdowns.value.filter((c) => c.id !== id)
      logger.info('countdown_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('countdown_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    countdowns,
    loading,
    error,
    sortedCountdowns,
    clearError,
    fetchAll,
    create,
    update,
    remove,
  }
})
