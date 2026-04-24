import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type {
  Recipe,
  RecipeCreate,
  RecipeUpdate,
  RecipeIngredientSearchResult,
  RecipeSuggestionRequest,
  RecipeSuggestionResponse,
  RecipeCandidate,
  RecipeStats,
  UrlImportRequest,
  UrlImportResponse,
  UrlImportCandidate,
  UrlImportSaveResult,
} from '@/api/client'

const logger = createLogger('RecipesStore')

export type IngredientMatch = 'any' | 'all'

export const useRecipesStore = defineStore('recipes', () => {
  const recipes = ref<Recipe[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const cuisineFilter = ref<string>('all')
  const mealTypeFilter = ref<string>('all')
  const difficultyFilter = ref<string>('all')
  const ratingMin = ref<number | null>(null)
  const searchQuery = ref('')
  const isSearchActive = ref(false)
  const sortField = ref<string>('name')
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const ingredientSearchResults = ref<RecipeIngredientSearchResult[]>([])
  const ingredientSearchActive = ref(false)
  const aiCandidates = ref<RecipeCandidate[]>([])
  const aiLoading = ref(false)
  const urlImportCandidate = ref<UrlImportCandidate | null>(null)
  const urlImportLoading = ref(false)

  const filteredRecipes = computed(() => {
    let result = recipes.value
    if (cuisineFilter.value !== 'all') {
      result = result.filter((r) => r.cuisine === cuisineFilter.value)
    }
    if (mealTypeFilter.value !== 'all') {
      result = result.filter((r) => r.meal_type === mealTypeFilter.value)
    }
    if (difficultyFilter.value !== 'all') {
      result = result.filter((r) => r.difficulty === difficultyFilter.value)
    }
    if (ratingMin.value !== null) {
      result = result.filter((r) => (r.rating ?? 0) >= (ratingMin.value ?? 0))
    }
    return result
  })

  const sortedRecipes = computed(() => {
    const sorted = [...filteredRecipes.value]
    const dir = sortDirection.value === 'asc' ? 1 : -1
    sorted.sort((a, b) => {
      switch (sortField.value) {
        case 'name':
          return dir * a.name.localeCompare(b.name)
        case 'total_time':
          return dir * ((a.total_time_minutes ?? 0) - (b.total_time_minutes ?? 0))
        case 'rating':
          return dir * ((a.rating ?? 0) - (b.rating ?? 0))
        case 'times_made':
          return dir * (a.times_made - b.times_made)
        case 'cuisine':
          return dir * (a.cuisine ?? '').localeCompare(b.cuisine ?? '')
        default:
          return 0
      }
    })
    return sorted
  })

  const cuisineCounts = computed(() => {
    const counts: Record<string, number> = { total: recipes.value.length }
    for (const r of recipes.value) {
      if (!r.cuisine) continue
      counts[r.cuisine] = (counts[r.cuisine] ?? 0) + 1
    }
    return counts
  })

  function clearError() {
    error.value = null
  }

  function setCuisineFilter(filter: string) {
    cuisineFilter.value = filter
  }

  function setMealTypeFilter(filter: string) {
    mealTypeFilter.value = filter
  }

  function setDifficultyFilter(filter: string) {
    difficultyFilter.value = filter
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
      const response = await api.get<Recipe[]>('/recipes/')
      recipes.value = response.data
      logger.info('recipes_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipes_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number, servings?: number): Promise<Recipe> {
    error.value = null
    try {
      const params = servings ? { servings } : undefined
      const response = await api.get<Recipe>(`/recipes/${id}/`, { params })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_fetch_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function create(input: RecipeCreate) {
    error.value = null
    try {
      const response = await api.post<Recipe>('/recipes/', input)
      recipes.value.push(response.data)
      logger.info('recipe_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: RecipeUpdate) {
    error.value = null
    try {
      const response = await api.patch<Recipe>(`/recipes/${id}/`, input)
      const index = recipes.value.findIndex((r) => r.id === id)
      if (index !== -1) {
        recipes.value[index] = response.data
      }
      logger.info('recipe_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_update_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/recipes/${id}/`)
      recipes.value = recipes.value.filter((r) => r.id !== id)
      logger.info('recipe_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_delete_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function markMade(id: number) {
    error.value = null
    try {
      const response = await api.post<Recipe>(`/recipes/${id}/mark-made/`)
      const index = recipes.value.findIndex((r) => r.id === id)
      if (index !== -1) {
        recipes.value[index] = response.data
      }
      logger.info('recipe_marked_made', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_mark_made_failed', { id, detail: apiError.detail })
      throw apiError
    }
  }

  async function search(query: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Recipe[]>('/recipes/search/', { params: { q: query } })
      recipes.value = response.data
      searchQuery.value = query
      isSearchActive.value = true
      logger.info('recipes_search', { query, count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipes_search_failed', { query, detail: apiError.detail })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function searchByIngredients(have: string[], match: IngredientMatch = 'any') {
    loading.value = true
    error.value = null
    ingredientSearchActive.value = true
    try {
      const response = await api.get<RecipeIngredientSearchResult[]>('/recipes/search-by-ingredients/', {
        params: { have: have.join(','), match },
      })
      ingredientSearchResults.value = response.data
      logger.info('recipes_ingredient_search', { count: response.data.length, match })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipes_ingredient_search_failed', { detail: apiError.detail })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function clearSearch() {
    searchQuery.value = ''
    isSearchActive.value = false
    ingredientSearchActive.value = false
    ingredientSearchResults.value = []
    await fetchAll()
  }

  async function fetchStats(): Promise<RecipeStats> {
    error.value = null
    try {
      const response = await api.get<RecipeStats>('/recipes/stats/')
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipes_stats_failed', { detail: apiError.detail })
      throw apiError
    }
  }

  async function aiSuggest(request: RecipeSuggestionRequest) {
    aiLoading.value = true
    error.value = null
    try {
      const response = await api.post<RecipeSuggestionResponse>('/recipes/ai-suggest/', request)
      aiCandidates.value = response.data.candidates
      logger.info('recipe_ai_suggest', { count: response.data.candidates.length })
      return response.data.candidates
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_ai_suggest_failed', { detail: apiError.detail })
      throw apiError
    } finally {
      aiLoading.value = false
    }
  }

  async function aiSave(candidate: RecipeCandidate) {
    error.value = null
    try {
      const response = await api.post<Recipe>('/recipes/ai-save/', candidate)
      recipes.value.push(response.data)
      aiCandidates.value = aiCandidates.value.filter((c) => c.source_url !== candidate.source_url)
      logger.info('recipe_ai_saved', { id: response.data.id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_ai_save_failed', { detail: apiError.detail })
      throw apiError
    }
  }

  function clearAICandidates() {
    aiCandidates.value = []
  }

  async function importFromUrl(request: UrlImportRequest) {
    urlImportLoading.value = true
    error.value = null
    try {
      const response = await api.post<UrlImportResponse>('/recipes/import-from-url/', request)
      urlImportCandidate.value = response.data.candidate
      logger.info('recipe_url_import_classified', { kind: response.data.candidate.kind })
      return response.data.candidate
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_url_import_failed', { detail: apiError.detail })
      throw apiError
    } finally {
      urlImportLoading.value = false
    }
  }

  async function saveUrlImport(candidate: UrlImportCandidate) {
    error.value = null
    try {
      const response = await api.post<UrlImportSaveResult>('/recipes/save-url-import/', candidate)
      if (response.data.recipe) recipes.value.push(response.data.recipe)
      urlImportCandidate.value = null
      logger.info('recipe_url_import_saved', {
        recipe_id: response.data.recipe?.id ?? null,
        technique_id: response.data.technique?.id ?? null,
      })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('recipe_url_import_save_failed', { detail: apiError.detail })
      throw apiError
    }
  }

  function clearUrlImportCandidate() {
    urlImportCandidate.value = null
  }

  return {
    recipes,
    loading,
    error,
    cuisineFilter,
    mealTypeFilter,
    difficultyFilter,
    ratingMin,
    searchQuery,
    isSearchActive,
    sortField,
    sortDirection,
    ingredientSearchResults,
    ingredientSearchActive,
    aiCandidates,
    aiLoading,
    filteredRecipes,
    sortedRecipes,
    cuisineCounts,
    clearError,
    setCuisineFilter,
    setMealTypeFilter,
    setDifficultyFilter,
    setRatingMin,
    setSort,
    fetchAll,
    fetchOne,
    create,
    update,
    remove,
    markMade,
    search,
    searchByIngredients,
    clearSearch,
    fetchStats,
    aiSuggest,
    aiSave,
    clearAICandidates,
    urlImportCandidate,
    urlImportLoading,
    importFromUrl,
    saveUrlImport,
    clearUrlImportCandidate,
  }
})
