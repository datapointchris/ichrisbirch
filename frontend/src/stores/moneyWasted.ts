import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { MoneyWasted, MoneyWastedCreate } from '@/api/client'

const logger = createLogger('MoneyWastedStore')

export const useMoneyWastedStore = defineStore('moneyWasted', () => {
  const items = ref<MoneyWasted[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedItems = computed(() => [...items.value].sort((a, b) => b.date_wasted.localeCompare(a.date_wasted)))

  const totalWasted = computed(() => items.value.reduce((sum, item) => sum + item.amount, 0))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<MoneyWasted[]>('/money-wasted/')
      items.value = response.data
      logger.info('money_wasted_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('money_wasted_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: MoneyWastedCreate) {
    error.value = null
    try {
      const response = await api.post<MoneyWasted>('/money-wasted/', input)
      items.value.push(response.data)
      logger.info('money_wasted_created', { id: response.data.id, item: response.data.item })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('money_wasted_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/money-wasted/${id}/`)
      items.value = items.value.filter((i) => i.id !== id)
      logger.info('money_wasted_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('money_wasted_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    items,
    loading,
    error,
    sortedItems,
    totalWasted,
    clearError,
    fetchAll,
    create,
    remove,
  }
})
