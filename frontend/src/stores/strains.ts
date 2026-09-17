import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Strain, StrainCreate, StrainUpdate, StrainVocabulary } from '@/api/client'

const logger = createLogger('StrainsStore')

export type StrainStatus = 'tried' | 'want_to_try'

export const STRAIN_STATUS_LABELS: Record<StrainStatus, string> = {
  tried: 'Tried',
  want_to_try: 'Want to Try',
}

// A vocabulary value is a lowercase key, and a couple of them are acronyms that
// title-casing mangles — 'cbd' reads as Cbd. The lookup tables carry no display
// column, so the spelling is decided here rather than fetched.
const STRAIN_ACRONYMS = new Set(['cbd', 'thc'])

/** Render a vocabulary key for a person: `sativa_dominant` to Sativa Dominant. */
export function humanizeStrainValue(value?: string): string {
  if (!value) return ''
  return value
    .split('_')
    .map((word) => (STRAIN_ACRONYMS.has(word) ? word.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(' ')
}

/** An empty vocabulary, so the view renders before the fetch lands. */
const EMPTY_VOCABULARY: StrainVocabulary = {
  types: [],
  statuses: [],
  effects: [],
  flavors: [],
  terpenes: [],
}

export const useStrainsStore = defineStore('strains', () => {
  const items = ref<Strain[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const sortField = ref<string>('name')
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const statusFilter = ref<string>('all')
  const typeFilter = ref<string>('all')
  const effectFilter = ref<string>('all')

  // Read from the API rather than declared here. The values are lookup tables,
  // so adding one is an insert on the server; a copy in this file would make it
  // a deploy of the frontend as well.
  const vocabulary = ref<StrainVocabulary>(EMPTY_VOCABULARY)

  const statusCounts = computed(() => {
    const counts = { tried: 0, want_to_try: 0, total: 0 }
    for (const strain of items.value) {
      if (strain.status === 'tried') counts.tried++
      else if (strain.status === 'want_to_try') counts.want_to_try++
      counts.total++
    }
    return counts
  })

  const filteredItems = computed(() => {
    let result = sortedItems.value
    if (statusFilter.value !== 'all') {
      result = result.filter((s) => s.status === statusFilter.value)
    }
    if (typeFilter.value !== 'all') {
      result = result.filter((s) => s.strain_type === typeFilter.value)
    }
    if (effectFilter.value !== 'all') {
      result = result.filter((s) => s.effects.includes(effectFilter.value))
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
        case 'strain_type':
          return dir * (a.strain_type ?? '').localeCompare(b.strain_type ?? '')
        case 'status':
          return dir * a.status.localeCompare(b.status)
        case 'thc_percent':
          return dir * ((a.thc_percent ?? 0) - (b.thc_percent ?? 0))
        case 'cbd_percent':
          return dir * ((a.cbd_percent ?? 0) - (b.cbd_percent ?? 0))
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

  function setSort(field: string) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'asc'
    }
  }

  function setStatusFilter(status: string) {
    statusFilter.value = status
  }

  function setTypeFilter(type: string) {
    typeFilter.value = type
  }

  function setEffectFilter(effect: string) {
    effectFilter.value = effect
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Strain[]>('/strains/')
      items.value = response.data
      logger.info('strains_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('strains_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchVocabulary() {
    error.value = null
    try {
      const response = await api.get<StrainVocabulary>('/strains/vocabulary/')
      vocabulary.value = response.data
      logger.info('strain_vocabulary_fetched', { effects: response.data.effects.length })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('strain_vocabulary_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function create(input: StrainCreate) {
    error.value = null
    try {
      const response = await api.post<Strain>('/strains/', input)
      items.value.push(response.data)
      logger.info('strain_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('strain_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: StrainUpdate) {
    error.value = null
    try {
      const response = await api.patch<Strain>(`/strains/${id}/`, input)
      const index = items.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      logger.info('strain_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('strain_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/strains/${id}/`)
      items.value = items.value.filter((s) => s.id !== id)
      logger.info('strain_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('strain_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    items,
    loading,
    error,
    sortField,
    sortDirection,
    statusFilter,
    typeFilter,
    effectFilter,
    vocabulary,
    statusCounts,
    filteredItems,
    sortedItems,
    clearError,
    setSort,
    setStatusFilter,
    setTypeFilter,
    setEffectFilter,
    fetchAll,
    fetchVocabulary,
    create,
    update,
    remove,
  }
})
