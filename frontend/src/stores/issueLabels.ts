import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { IssueLabel, IssueLabelCreate, IssueLabelUpdate } from '@/api/client'

const logger = createLogger('IssueLabelsStore')

export const useIssueLabelsStore = defineStore('issueLabels', () => {
  const items = ref<IssueLabel[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  /** The group names in use, so a new label can join one without retyping it. */
  const groups = computed(() => [...new Set(items.value.flatMap((label) => (label.group_slug ? [label.group_slug] : [])))].sort())

  function wrapError(e: unknown): ApiError {
    return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<IssueLabel[]>('/issues/labels/')
      items.value = response.data
      logger.info('issue_labels_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issue_labels_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function write<T>(action: string, slug: string, request: () => Promise<T>): Promise<T> {
    error.value = null
    let result: T
    try {
      result = await request()
      logger.info('issue_label_write', { action, slug })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issue_label_write_failed', { action, slug, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
    try {
      await fetchAll()
    } catch {
      logger.warning('issue_labels_refresh_failed')
    }
    return result
  }

  function create(input: IssueLabelCreate) {
    return write('create', input.slug, async () => (await api.post<IssueLabel>('/issues/labels/', input)).data)
  }

  function update(slug: string, input: IssueLabelUpdate) {
    return write('update', slug, async () => (await api.patch<IssueLabel>(`/issues/labels/${slug}/`, input)).data)
  }

  function remove(slug: string) {
    return write('delete', slug, async () => {
      await api.delete(`/issues/labels/${slug}/`)
    })
  }

  return {
    items,
    loading,
    error,
    groups,
    fetchAll,
    create,
    update,
    remove,
  }
})
