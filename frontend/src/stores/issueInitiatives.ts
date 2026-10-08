import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Initiative, InitiativeCreate, InitiativeStatus, InitiativeUpdate } from '@/api/client'

const logger = createLogger('IssueInitiativesStore')

export type InitiativeStatusFilter = InitiativeStatus | 'all'

export const INITIATIVE_STATUS_LABELS: Record<InitiativeStatus, string> = {
  active: 'Active',
  completed: 'Completed',
  dropped: 'Dropped',
}

export const useIssueInitiativesStore = defineStore('issueInitiatives', () => {
  const items = ref<Initiative[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const statusFilter = ref<InitiativeStatusFilter>('active')

  function wrapError(e: unknown): ApiError {
    return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Initiative[]>('/issues/initiatives/', { params: { status: statusFilter.value } })
      items.value = response.data
      logger.info('initiatives_fetched', { count: response.data.length, status: statusFilter.value })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('initiatives_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function setStatusFilter(status: InitiativeStatusFilter) {
    statusFilter.value = status
    await fetchAll()
  }

  // The counts and the order both move with a write, so each is followed by a
  // fresh list. A failed re-read is not the write failing.
  async function write<T>(action: string, context: Record<string, unknown>, request: () => Promise<T>): Promise<T> {
    error.value = null
    let result: T
    try {
      result = await request()
      logger.info('initiative_write', { action, ...context })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('initiative_write_failed', { action, ...context, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
    try {
      await fetchAll()
    } catch {
      logger.warning('initiatives_refresh_failed')
    }
    return result
  }

  function create(input: InitiativeCreate) {
    return write('create', { name: input.name }, async () => (await api.post<Initiative>('/issues/initiatives/', input)).data)
  }

  function update(initiative: Initiative, input: InitiativeUpdate) {
    return write(
      'update',
      { id: initiative.id, fields: Object.keys(input) },
      async () => (await api.patch<Initiative>(`/issues/initiatives/${initiative.id}/`, input)).data
    )
  }

  /** Dropping takes a reason; completing and reopening take none. */
  function setStatus(initiative: Initiative, status: InitiativeStatus, reason?: string) {
    const input: InitiativeUpdate = { status }
    if (reason !== undefined) input.status_reason = reason
    return update(initiative, input)
  }

  function remove(initiative: Initiative) {
    return write('delete', { id: initiative.id }, async () => {
      await api.delete(`/issues/initiatives/${initiative.id}/`)
    })
  }

  return {
    items,
    loading,
    error,
    statusFilter,
    fetchAll,
    setStatusFilter,
    create,
    update,
    setStatus,
    remove,
  }
})
