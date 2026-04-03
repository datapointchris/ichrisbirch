import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { AutoFun, AutoFunCreate, AutoFunUpdate } from '@/api/types'

const logger = createLogger('AutoFunStore')

export const useAutoFunStore = defineStore('autofun', () => {
  const items = ref<AutoFun[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const activeItems = computed(() => items.value.filter((i) => !i.is_completed))
  const completedItems = computed(() => items.value.filter((i) => i.is_completed))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<AutoFun[]>('/autofun/')
      items.value = response.data
      logger.info('autofun_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autofun_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: AutoFunCreate) {
    error.value = null
    try {
      const response = await api.post<AutoFun>('/autofun/', input)
      items.value.unshift(response.data)
      logger.info('autofun_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autofun_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: AutoFunUpdate) {
    error.value = null
    try {
      const response = await api.patch<AutoFun>(`/autofun/${id}/`, input)
      const index = items.value.findIndex((i) => i.id === id)
      if (index !== -1) items.value[index] = response.data
      logger.info('autofun_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autofun_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/autofun/${id}/`)
      items.value = items.value.filter((i) => i.id !== id)
      logger.info('autofun_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('autofun_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    items,
    loading,
    error,
    activeItems,
    completedItems,
    clearError,
    fetchAll,
    create,
    update,
    remove,
  }
})
