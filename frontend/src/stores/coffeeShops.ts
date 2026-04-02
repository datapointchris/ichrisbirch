import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { CoffeeShop, CoffeeShopCreate, CoffeeShopUpdate } from '@/api/client'

const logger = createLogger('CoffeeShopsStore')

export const useCoffeeShopsStore = defineStore('coffeeShops', () => {
  const items = ref<CoffeeShop[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const sortField = ref<string>('name')
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const filterCity = ref<string>('all')

  const cities = computed(() => {
    const citySet = new Set(items.value.map((s) => s.city).filter((c): c is string => Boolean(c)))
    return Array.from(citySet).sort()
  })

  const filteredItems = computed(() => {
    if (filterCity.value === 'all') return sortedItems.value
    return sortedItems.value.filter((s) => s.city === filterCity.value)
  })

  const sortedItems = computed(() => {
    const sorted = [...items.value]
    const dir = sortDirection.value === 'asc' ? 1 : -1
    sorted.sort((a, b) => {
      switch (sortField.value) {
        case 'name':
          return dir * a.name.localeCompare(b.name)
        case 'rating':
          return dir * ((a.rating ?? 0) - (b.rating ?? 0))
        case 'city':
          return dir * (a.city ?? '').localeCompare(b.city ?? '')
        case 'date_visited':
          return dir * (a.date_visited ?? '').localeCompare(b.date_visited ?? '')
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

  function setFilterCity(city: string) {
    filterCity.value = city
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<CoffeeShop[]>('/coffee/shops/')
      items.value = response.data
      logger.info('coffee_shops_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_shops_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: CoffeeShopCreate) {
    error.value = null
    try {
      const response = await api.post<CoffeeShop>('/coffee/shops/', input)
      items.value.push(response.data)
      logger.info('coffee_shop_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_shop_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: CoffeeShopUpdate) {
    error.value = null
    try {
      const response = await api.patch<CoffeeShop>(`/coffee/shops/${id}/`, input)
      const index = items.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      logger.info('coffee_shop_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_shop_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/coffee/shops/${id}/`)
      items.value = items.value.filter((s) => s.id !== id)
      logger.info('coffee_shop_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('coffee_shop_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    items,
    loading,
    error,
    sortField,
    sortDirection,
    filterCity,
    cities,
    filteredItems,
    sortedItems,
    clearError,
    setSort,
    setFilterCity,
    fetchAll,
    create,
    update,
    remove,
  }
})
