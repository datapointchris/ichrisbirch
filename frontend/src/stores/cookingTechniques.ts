import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { CookingTechnique, CookingTechniqueCreate, CookingTechniqueUpdate, CookingTechniqueCategoryBreakdown } from '@/api/client'

const logger = createLogger('CookingTechniquesStore')

const ENDPOINT = '/recipes/cooking-techniques/'

export const useCookingTechniquesStore = defineStore('cookingTechniques', () => {
  const techniques = ref<CookingTechnique[]>([])
  const categories = ref<CookingTechniqueCategoryBreakdown[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const categoryFilter = ref<string>('all')
  const ratingMin = ref<number | null>(null)
  const searchQuery = ref('')
  const isSearchActive = ref(false)
  const sortField = ref<string>('name')
  const sortDirection = ref<'asc' | 'desc'>('asc')

  const filteredTechniques = computed(() => {
    let result = techniques.value
    if (categoryFilter.value !== 'all') {
      result = result.filter((t) => t.category === categoryFilter.value)
    }
    if (ratingMin.value !== null) {
      result = result.filter((t) => (t.rating ?? 0) >= (ratingMin.value ?? 0))
    }
    return result
  })

  const sortedTechniques = computed(() => {
    const sorted = [...filteredTechniques.value]
    const dir = sortDirection.value === 'asc' ? 1 : -1
    sorted.sort((a, b) => {
      switch (sortField.value) {
        case 'name':
          return dir * a.name.localeCompare(b.name)
        case 'category':
          return dir * a.category.localeCompare(b.category)
        case 'rating':
          return dir * ((a.rating ?? 0) - (b.rating ?? 0))
        default:
          return 0
      }
    })
    return sorted
  })

  function clearError() {
    error.value = null
  }

  function setCategoryFilter(filter: string) {
    categoryFilter.value = filter
  }

  function setRatingMin(value: number | null) {
    ratingMin.value = value
  }

  function setSort(field: string) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'asc'
    }
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<CookingTechnique[]>(ENDPOINT)
      techniques.value = response.data
      logger.info('cooking_techniques_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_techniques_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number): Promise<CookingTechnique> {
    error.value = null
    try {
      const response = await api.get<CookingTechnique>(`${ENDPOINT}${id}/`)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_fetch_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function fetchBySlug(slug: string): Promise<CookingTechnique> {
    error.value = null
    try {
      const response = await api.get<CookingTechnique>(`${ENDPOINT}slug/${slug}/`)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_slug_fetch_failed', { slug, detail: apiError.detail })
      throw apiError
    }
  }

  async function fetchCategories() {
    error.value = null
    try {
      const response = await api.get<CookingTechniqueCategoryBreakdown[]>(`${ENDPOINT}categories/`)
      categories.value = response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_categories_fetch_failed', { detail: apiError.detail })
      throw apiError
    }
  }

  async function create(input: CookingTechniqueCreate) {
    error.value = null
    try {
      const response = await api.post<CookingTechnique>(ENDPOINT, input)
      techniques.value.push(response.data)
      logger.info('cooking_technique_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: CookingTechniqueUpdate) {
    error.value = null
    try {
      const response = await api.patch<CookingTechnique>(`${ENDPOINT}${id}/`, input)
      const index = techniques.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        techniques.value[index] = response.data
      }
      logger.info('cooking_technique_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_update_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`${ENDPOINT}${id}/`)
      techniques.value = techniques.value.filter((t) => t.id !== id)
      logger.info('cooking_technique_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_technique_delete_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function search(query: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<CookingTechnique[]>(`${ENDPOINT}search/`, { params: { q: query } })
      techniques.value = response.data
      searchQuery.value = query
      isSearchActive.value = true
      logger.info('cooking_techniques_search', { query, count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('cooking_techniques_search_failed', { query, detail: apiError.detail })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function clearSearch() {
    searchQuery.value = ''
    isSearchActive.value = false
    await fetchAll()
  }

  return {
    techniques,
    categories,
    loading,
    error,
    categoryFilter,
    ratingMin,
    searchQuery,
    isSearchActive,
    sortField,
    sortDirection,
    filteredTechniques,
    sortedTechniques,
    clearError,
    setCategoryFilter,
    setRatingMin,
    setSort,
    fetchAll,
    fetchOne,
    fetchBySlug,
    fetchCategories,
    create,
    update,
    remove,
    search,
    clearSearch,
  }
})
