import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { AutoTask, AutoTaskCreate, AutoTaskUpdate, TaskCategory, AutoTaskFrequency } from '@/api/client'

const logger = createLogger('AutoTasksStore')

export const TASK_CATEGORIES: TaskCategory[] = [
  'Automotive',
  'Chore',
  'Computer',
  'Dingo',
  'Financial',
  'Home',
  'Kitchen',
  'Learn',
  'Personal',
  'Purchase',
  'Research',
  'Work',
]

export const AUTOTASK_FREQUENCIES: AutoTaskFrequency[] = ['Daily', 'Weekly', 'Biweekly', 'Monthly', 'Quarterly', 'Semiannually', 'Yearly']

export const useAutoTasksStore = defineStore('autotasks', () => {
  const autotasks = ref<AutoTask[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedAutoTasks = computed(() => [...autotasks.value].sort((a, b) => b.last_run_date.localeCompare(a.last_run_date)))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<AutoTask[]>('/autotasks/')
      autotasks.value = response.data
      logger.info('autotasks_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autotasks_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: AutoTaskCreate) {
    error.value = null
    try {
      const response = await api.post<AutoTask>('/autotasks/', input)
      autotasks.value.push(response.data)
      logger.info('autotask_created', { id: response.data.id, name: response.data.name })
      // Replicate Flask behavior: immediately run after creation
      const updated = await run(response.data.id)
      return updated
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autotask_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function run(id: number) {
    error.value = null
    try {
      const response = await api.patch<AutoTask>(`/autotasks/${id}/run/`)
      const index = autotasks.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        autotasks.value[index] = response.data
      }
      logger.info('autotask_ran', { id, run_count: response.data.run_count })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autotask_run_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: AutoTaskUpdate) {
    error.value = null
    try {
      const response = await api.patch<AutoTask>(`/autotasks/${id}/`, input)
      const index = autotasks.value.findIndex((a) => a.id === id)
      if (index !== -1) autotasks.value[index] = response.data
      logger.info('autotask_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autotask_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/autotasks/${id}/`)
      autotasks.value = autotasks.value.filter((a) => a.id !== id)
      logger.info('autotask_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autotask_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    autotasks,
    loading,
    error,
    sortedAutoTasks,
    clearError,
    fetchAll,
    create,
    update,
    run,
    remove,
  }
})
