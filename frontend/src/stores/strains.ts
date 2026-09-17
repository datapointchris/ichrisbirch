import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Strain, StrainCreate, StrainUpdate, StrainVocabulary, StrainFilters } from '@/api/client'

const logger = createLogger('StrainsStore')

/**
 * The two statuses, compiled in.
 *
 * `status` is a closed lifecycle and is the one vocabulary this page does not
 * read from the server. Each value needs a counter, a filter, a row color and a
 * label, and a lookup table carrying only a name supplies none of them. Adding
 * a third is a code change here, in `_strains.scss` and in the model — see
 * `ichrisbirch/models/strain.py` for the trade. The other four vocabularies are
 * open sets and are fetched.
 */
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
  strain_type: [],
  status: [],
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
  // a deploy of the frontend as well. `status` is the exception, above.
  const vocabulary = ref<StrainVocabulary>(EMPTY_VOCABULARY)

  /**
   * Counts per status, read from the vocabulary rather than from the loaded rows.
   *
   * The rows are a filtered page, so counting them would make each counter
   * report the narrowing rather than the catalog — and clicking one would then
   * change the others.
   */
  const statusCounts = computed<Record<string, number>>(() => {
    const counts: Record<string, number> = { tried: 0, want_to_try: 0, total: 0 }
    for (const entry of vocabulary.value.status) {
      counts[entry.name] = entry.count
    }
    counts.total = vocabulary.value.status.reduce((sum, entry) => sum + entry.count, 0)
    return counts
  })

  /**
   * The rows to render, sorted. Narrowing is the server's — `filters()` is sent
   * to `GET /strains/`, which is where the CLI's filters resolve too, so one
   * definition answers both.
   */
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

  /** The filters currently set, in the shape `GET /strains/` takes. */
  function filters(): StrainFilters {
    const selected: StrainFilters = {}
    if (statusFilter.value !== 'all') selected.status = statusFilter.value
    if (typeFilter.value !== 'all') selected.strain_type = typeFilter.value
    if (effectFilter.value !== 'all') selected.effect = effectFilter.value
    return selected
  }

  /** The filters currently set, named for an empty state. */
  const activeFilters = computed(() => {
    const active: string[] = []
    if (statusFilter.value !== 'all') active.push(`status ${statusFilter.value}`)
    if (typeFilter.value !== 'all') active.push(`type ${typeFilter.value}`)
    if (effectFilter.value !== 'all') active.push(`effect ${effectFilter.value}`)
    return active
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

  async function setStatusFilter(status: string) {
    statusFilter.value = status
    await fetchAll()
  }

  async function setTypeFilter(type: string) {
    typeFilter.value = type
    await fetchAll()
  }

  async function setEffectFilter(effect: string) {
    effectFilter.value = effect
    await fetchAll()
  }

  function wrapError(e: unknown): ApiError {
    return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Strain[]>('/strains/', { params: filters() })
      items.value = response.data
      logger.info('strains_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = wrapError(e)
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
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('strain_vocabulary_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  /**
   * Re-read the counts after a write.
   *
   * Every count on the page comes from the vocabulary, so a create that adds a
   * sleepy strain leaves `Sleepy (N)` at the old N until this runs. Failure is
   * swallowed: the write succeeded, and a stale count is not worth turning that
   * into an error the user sees.
   */
  async function refreshCounts() {
    try {
      await fetchVocabulary()
    } catch {
      logger.warning('strain_vocabulary_refresh_failed')
    }
  }

  async function create(input: StrainCreate) {
    error.value = null
    try {
      const response = await api.post<Strain>('/strains/', input)
      items.value.push(response.data)
      logger.info('strain_created', { id: response.data.id, name: response.data.name })
      await refreshCounts()
      return response.data
    } catch (e) {
      const apiError = wrapError(e)
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
      await refreshCounts()
      return response.data
    } catch (e) {
      const apiError = wrapError(e)
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
      await refreshCounts()
    } catch (e) {
      const apiError = wrapError(e)
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
    activeFilters,
    sortedItems,
    filters,
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
