import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { CoffeeBean, CoffeeBeanCreate, CoffeeBeanUpdate } from '@/api/client'

const logger = createLogger('CoffeeBeansStore')

export const ROAST_LEVELS = ['light', 'medium-light', 'medium', 'medium-dark', 'dark'] as const
export const BREW_METHODS = ['pour-over', 'espresso', 'french-press', 'aeropress', 'cold-brew', 'drip', 'moka-pot'] as const

export const useCoffeeBeansStore = defineStore('coffeeBeans', () => {
  const items = ref<CoffeeBean[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const sortField = ref<string>('name')
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const roastLevelFilter = ref<string>('all')
  const brewMethodFilter = ref<string>('all')

  const filteredItems = computed(() => {
    let result = sortedItems.value
    if (roastLevelFilter.value !== 'all') {
      result = result.filter((b) => b.roast_level === roastLevelFilter.value)
    }
    if (brewMethodFilter.value !== 'all') {
      result = result.filter((b) => b.brew_method === brewMethodFilter.value)
    }
    return result
  })

  const sortedItems = computed(() => {
    const sorted = [...items.value]
    const dir = sortDirection.value === 'asc' ? 1 : -1
    sorted.sort((a, b) => {
      switch (sortField.value) {
        case 'name':
          return dir * a.name.localeCompare(b.name)
        case 'roaster':
          return dir * (a.roaster ?? '').localeCompare(b.roaster ?? '')
        case 'origin':
          return dir * (a.origin ?? '').localeCompare(b.origin ?? '')
        case 'rating':
          return dir * ((a.rating ?? 0) - (b.rating ?? 0))
        case 'price':
          return dir * ((a.price ?? 0) - (b.price ?? 0))
        case 'purchase_date':
          return dir * (a.purchase_date ?? '').localeCompare(b.purchase_date ?? '')
        default:
          return 0
      }
    })
    return sorted
  })

  function clearError() {
    error.value = null
  }

  function setSort(field: string) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'asc'
    }
  }

  function setRoastLevelFilter(level: string) {
    roastLevelFilter.value = level
  }

  function setBrewMethodFilter(method: string) {
    brewMethodFilter.value = method
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<CoffeeBean[]>('/coffee/beans/')
      items.value = response.data
      logger.info('coffee_beans_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_beans_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: CoffeeBeanCreate) {
    error.value = null
    try {
      const response = await api.post<CoffeeBean>('/coffee/beans/', input)
      items.value.push(response.data)
      logger.info('coffee_bean_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_bean_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: CoffeeBeanUpdate) {
    error.value = null
    try {
      const response = await api.patch<CoffeeBean>(`/coffee/beans/${id}/`, input)
      const index = items.value.findIndex((b) => b.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      logger.info('coffee_bean_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_bean_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/coffee/beans/${id}/`)
      items.value = items.value.filter((b) => b.id !== id)
      logger.info('coffee_bean_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_bean_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    items,
    loading,
    error,
    sortField,
    sortDirection,
    roastLevelFilter,
    brewMethodFilter,
    filteredItems,
    sortedItems,
    clearError,
    setSort,
    setRoastLevelFilter,
    setBrewMethodFilter,
    fetchAll,
    create,
    update,
    remove,
  }
})
