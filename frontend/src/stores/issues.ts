import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type {
  Issue,
  IssueComment,
  IssueCreate,
  IssueDetail,
  IssueFilters,
  IssueRankMove,
  IssueStatus,
  IssueSummary,
  IssueUpdate,
  IssueVocabulary,
} from '@/api/client'

const logger = createLogger('IssuesStore')

/** `unclosed` is the API's default list, sent as no status at all. */
export type IssueStatusFilter = 'unclosed' | IssueStatus | 'all'

/**
 * A slice of the loaded rows, cut by the flags the server derived on the read.
 *
 * `ready` is the agent queue: the server's `is_ready` without decisions, which
 * wait on a person rather than an agent. `decisions` is that same set of
 * person-shaped work, so it is the one lens with nothing an agent can take.
 */
export type IssueLens = 'all' | 'ready' | 'in_progress' | 'blocked' | 'triage' | 'decisions'

export const ISSUE_LENSES: IssueLens[] = ['all', 'ready', 'in_progress', 'blocked', 'triage', 'decisions']

export const ISSUE_LENS_LABELS: Record<IssueLens, string> = {
  all: 'All',
  ready: 'Ready',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  triage: 'Triage',
  decisions: 'Decisions',
}

export const ISSUE_STATUS_LABELS: Record<IssueStatus, string> = {
  triage: 'Triage',
  open: 'Open',
  in_progress: 'In Progress',
  completed: 'Completed',
  canceled: 'Canceled',
}

/** The filters a page sets, each naming the `GET /issues/` parameter it becomes. */
export type IssueFilterKey = 'status' | 'repo' | 'type' | 'label' | 'initiative' | 'priority'

/** A repo filter of this value asks for the issues that name no repo. */
export const NO_REPO = ''

/** A priority's name from the vocabulary, or the number while the vocabulary has not landed. */
export function priorityLabel(vocabulary: IssueVocabulary, value: number): string {
  return vocabulary.priorities.find((entry) => entry.value === value)?.name ?? String(value)
}

export function isClosedIssue(issue: { status: IssueStatus }): boolean {
  return issue.status === 'completed' || issue.status === 'canceled'
}

export function inLens(issue: Issue, lens: IssueLens): boolean {
  switch (lens) {
    case 'ready':
      return issue.is_ready && issue.type !== 'decision'
    case 'in_progress':
      return issue.status === 'in_progress'
    case 'blocked':
      return issue.is_blocked
    case 'triage':
      return issue.status === 'triage'
    case 'decisions':
      return issue.type === 'decision' && !isClosedIssue(issue)
    default:
      return true
  }
}

const EMPTY_VOCABULARY: IssueVocabulary = {
  statuses: [],
  types: [],
  priorities: [],
  initiative_statuses: [],
  labels: [],
}

export const useIssuesStore = defineStore('issues', () => {
  const items = ref<Issue[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const vocabulary = ref<IssueVocabulary>(EMPTY_VOCABULARY)

  const statusFilter = ref<IssueStatusFilter>('unclosed')
  const repoFilter = ref('all')
  const typeFilter = ref('all')
  const labelFilter = ref('all')
  const initiativeFilter = ref('all')
  const priorityFilter = ref('all')
  const search = ref('')
  const lens = ref<IssueLens>('all')

  // Repos are no vocabulary on the server, so the choices are the repos the
  // unfiltered list names. They are kept while a repo filter narrows the rows,
  // or picking one repo would leave it the only choice.
  const knownRepos = ref<string[]>([])

  const expandedId = ref<string | null>(null)
  const detail = ref<IssueDetail | null>(null)

  const filterRefs = {
    status: statusFilter,
    repo: repoFilter,
    type: typeFilter,
    label: labelFilter,
    initiative: initiativeFilter,
    priority: priorityFilter,
  }

  const lensCounts = computed<Record<IssueLens, number>>(() => {
    const counts = Object.fromEntries(ISSUE_LENSES.map((name) => [name, 0])) as Record<IssueLens, number>
    for (const issue of items.value) {
      for (const name of ISSUE_LENSES) {
        if (inLens(issue, name)) counts[name] += 1
      }
    }
    return counts
  })

  /** The rows the lens keeps, in the order the server sent them. */
  const visibleItems = computed(() => items.value.filter((issue) => inLens(issue, lens.value)))

  /** The narrowing in force, named for an empty state. */
  const activeFilters = computed(() => {
    const active: string[] = []
    if (statusFilter.value !== 'unclosed') active.push(`status ${statusFilter.value}`)
    if (repoFilter.value !== 'all') active.push(repoFilter.value === NO_REPO ? 'no repo' : `repo ${repoFilter.value}`)
    if (typeFilter.value !== 'all') active.push(`type ${typeFilter.value}`)
    if (labelFilter.value !== 'all') active.push(`label ${labelFilter.value}`)
    if (initiativeFilter.value !== 'all') active.push(`initiative ${initiativeFilter.value}`)
    if (priorityFilter.value !== 'all') active.push(`priority ${priorityLabel(vocabulary.value, Number(priorityFilter.value))}`)
    if (search.value.trim()) active.push(`"${search.value.trim()}"`)
    if (lens.value !== 'all') active.push(ISSUE_LENS_LABELS[lens.value].toLowerCase())
    return active
  })

  /** The filters currently set, in the shape `GET /issues/` takes. */
  function filters(): IssueFilters {
    const selected: IssueFilters = {}
    if (statusFilter.value !== 'unclosed') selected.status = statusFilter.value
    if (repoFilter.value !== 'all') selected.repo = repoFilter.value
    if (typeFilter.value !== 'all') selected.type = typeFilter.value
    if (labelFilter.value !== 'all') selected.label = labelFilter.value
    if (initiativeFilter.value !== 'all') selected.initiative = initiativeFilter.value
    if (priorityFilter.value !== 'all') selected.priority = Number(priorityFilter.value)
    const text = search.value.trim()
    if (text) selected.search = text
    return selected
  }

  function wrapError(e: unknown): ApiError {
    return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
  }

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Issue[]>('/issues/', { params: filters() })
      items.value = response.data
      if (repoFilter.value === 'all') {
        knownRepos.value = [...new Set(response.data.flatMap((issue) => (issue.repo ? [issue.repo] : [])))].sort()
      }
      logger.info('issues_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issues_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchVocabulary() {
    try {
      const response = await api.get<IssueVocabulary>('/issues/vocabulary/')
      vocabulary.value = response.data
      logger.info('issue_vocabulary_fetched', { labels: response.data.labels.length })
      return response.data
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issue_vocabulary_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function fetchDetail(number: number) {
    const response = await api.get<IssueDetail>(`/issues/${number}/`)
    detail.value = response.data
    return response.data
  }

  /** Every filter back to its default, without reading. */
  function resetFilters() {
    statusFilter.value = 'unclosed'
    for (const key of ['repo', 'type', 'label', 'initiative', 'priority'] as const) filterRefs[key].value = 'all'
    search.value = ''
    lens.value = 'all'
  }

  /** Set filters without reading, for a page applying several at once before its first fetch. */
  function setFilters(values: Partial<Record<IssueFilterKey, string>>) {
    for (const [key, value] of Object.entries(values)) {
      if (value !== undefined) filterRefs[key as IssueFilterKey].value = value
    }
  }

  async function setFilter(key: IssueFilterKey, value: string) {
    filterRefs[key].value = value
    await fetchAll()
  }

  async function setSearch(text: string) {
    search.value = text
    await fetchAll()
  }

  function setLens(name: IssueLens) {
    lens.value = name
  }

  async function toggleDetail(issue: Issue) {
    if (expandedId.value === issue.id) {
      expandedId.value = null
      detail.value = null
      return
    }
    expandedId.value = issue.id
    detail.value = null
    try {
      await fetchDetail(issue.number)
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issue_detail_fetch_failed', { number: issue.number, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  /**
   * Re-read everything a write can move.
   *
   * Closing one issue unblocks the issues waiting on it and changes the
   * priority its blockers inherit, so a write is followed by a fresh list
   * rather than a patch of the one row. A failed re-read is logged and left on
   * `error`: the write itself succeeded, and reporting it as failed would be wrong.
   */
  async function refreshAfterWrite() {
    const expanded = expandedId.value ? items.value.find((issue) => issue.id === expandedId.value) : undefined
    try {
      await Promise.all([fetchAll(), fetchVocabulary()])
      if (expanded && items.value.some((issue) => issue.id === expanded.id)) {
        await fetchDetail(expanded.number)
      } else if (expanded) {
        expandedId.value = null
        detail.value = null
      }
    } catch {
      logger.warning('issues_refresh_failed')
    }
  }

  async function write<T>(action: string, context: Record<string, unknown>, request: () => Promise<T>): Promise<T> {
    error.value = null
    let result: T
    try {
      result = await request()
      logger.info('issue_write', { action, ...context })
    } catch (e) {
      const apiError = wrapError(e)
      error.value = apiError
      logger.error('issue_write_failed', { action, ...context, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
    await refreshAfterWrite()
    return result
  }

  function create(input: IssueCreate) {
    return write('create', { title: input.title }, async () => (await api.post<IssueDetail>('/issues/', input)).data)
  }

  function update(issue: Issue, input: IssueUpdate) {
    return write(
      'update',
      { number: issue.number, fields: Object.keys(input) },
      async () => (await api.patch<IssueDetail>(`/issues/${issue.number}/`, input)).data
    )
  }

  /** A status change through PATCH, carrying what the move needs: a cancel's reason or duplicate. */
  function setStatus(issue: Issue, status: IssueStatus, extra: Omit<IssueUpdate, 'status'> = {}) {
    return update(issue, { ...extra, status })
  }

  function release(issue: Issue) {
    return write('release', { number: issue.number }, async () => (await api.delete<Issue>(`/issues/${issue.number}/claim/`)).data)
  }

  function move(issue: Issue, placement: IssueRankMove) {
    return write(
      'rank',
      { number: issue.number, ...placement },
      async () => (await api.post<Issue>(`/issues/${issue.number}/rank/`, placement)).data
    )
  }

  function addDependency(issue: Issue, dependsOn: number) {
    return write(
      'add_dependency',
      { number: issue.number, depends_on: dependsOn },
      async () => (await api.post<IssueDetail>(`/issues/${issue.number}/dependencies/`, { depends_on: dependsOn })).data
    )
  }

  function removeDependency(issue: Issue, dependsOn: IssueSummary) {
    return write('remove_dependency', { number: issue.number, depends_on: dependsOn.number }, async () => {
      await api.delete(`/issues/${issue.number}/dependencies/${dependsOn.number}/`)
    })
  }

  function addComment(issue: Issue, body: string, author?: string) {
    return write(
      'add_comment',
      { number: issue.number },
      async () => (await api.post<IssueComment>(`/issues/${issue.number}/comments/`, { body, author })).data
    )
  }

  function removeComment(issue: Issue, comment: IssueComment) {
    return write('remove_comment', { number: issue.number, comment: comment.id }, async () => {
      await api.delete(`/issues/${issue.number}/comments/${comment.id}/`)
    })
  }

  function remove(issue: Issue) {
    if (expandedId.value === issue.id) {
      expandedId.value = null
      detail.value = null
    }
    return write('delete', { number: issue.number }, async () => {
      await api.delete(`/issues/${issue.number}/`)
    })
  }

  return {
    items,
    loading,
    error,
    vocabulary,
    statusFilter,
    repoFilter,
    typeFilter,
    labelFilter,
    initiativeFilter,
    priorityFilter,
    search,
    lens,
    knownRepos,
    expandedId,
    detail,
    lensCounts,
    visibleItems,
    activeFilters,
    filters,
    clearError,
    fetchAll,
    fetchVocabulary,
    fetchDetail,
    resetFilters,
    setFilters,
    setFilter,
    setSearch,
    setLens,
    toggleDetail,
    create,
    update,
    setStatus,
    release,
    move,
    addDependency,
    removeDependency,
    addComment,
    removeComment,
    remove,
  }
})
