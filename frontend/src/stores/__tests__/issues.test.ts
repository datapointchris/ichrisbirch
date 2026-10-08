import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIssuesStore, inLens } from '../issues'
import { ApiError } from '@/api/errors'
import type { Issue, IssueDetail, IssueVocabulary } from '@/api/client'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/api/client'
const mockApi = vi.mocked(api)

function makeIssue(overrides: Partial<Issue>): Issue {
  return {
    id: `id-${overrides.number ?? 1}`,
    number: 1,
    title: 'An issue',
    description: null,
    acceptance: null,
    repo: 'ichrisbirch',
    type: 'task',
    status: 'open',
    status_reason: null,
    priority: 0,
    effective_priority: 0,
    rank: 1,
    deferred_until_date: null,
    claimed_by: null,
    claim_expires_ts: null,
    initiative: null,
    parent: null,
    discovered_from: null,
    duplicate_of: null,
    labels: [],
    depends_on: [],
    blocks: [],
    child_count: 0,
    open_child_count: 0,
    comment_count: 0,
    is_blocked: false,
    is_ready: true,
    created_ts: '2026-10-01T12:00:00Z',
    updated_ts: '2026-10-01T12:00:00Z',
    closed_ts: null,
    ...overrides,
  }
}

// One row for each lens: ready work, a claim, a blocked issue, triage, and a
// decision that the server reports as ready but no agent should take.
const ready = makeIssue({ number: 10, title: 'Ready task' })
const claimed = makeIssue({ number: 11, status: 'in_progress', claimed_by: 'claude-code/abc', is_ready: false })
const blocked = makeIssue({
  number: 12,
  is_blocked: true,
  is_ready: false,
  depends_on: [{ id: 'id-10', number: 10, title: 'Ready task', status: 'open' }],
})
const triage = makeIssue({ number: 13, status: 'triage', is_ready: false })
const decision = makeIssue({ number: 14, type: 'decision', title: 'Pick a scheme' })
const testIssues = [ready, claimed, blocked, triage, decision]

const testVocabulary: IssueVocabulary = {
  statuses: ['triage', 'open', 'in_progress', 'completed', 'canceled'],
  types: ['bug', 'feature', 'task', 'chore', 'decision'],
  priorities: [
    { value: 0, name: 'none' },
    { value: 1, name: 'urgent' },
    { value: 2, name: 'high' },
    { value: 3, name: 'medium' },
    { value: 4, name: 'low' },
  ],
  initiative_statuses: ['active', 'completed', 'dropped'],
  labels: [{ slug: 'area-cli', group_slug: 'area', description: null, open_issue_count: 1 }],
}

function detailOf(issue: Issue): IssueDetail {
  return { ...issue, children: [], comments: [] }
}

describe('inLens', () => {
  it('keeps a decision out of the ready lens though the server calls it ready', () => {
    expect(decision.is_ready).toBe(true)
    expect(inLens(decision, 'ready')).toBe(false)
    expect(inLens(decision, 'decisions')).toBe(true)
  })

  it('drops a closed decision from the decisions lens', () => {
    expect(inLens(makeIssue({ type: 'decision', status: 'completed' }), 'decisions')).toBe(false)
  })

  it('puts every row in the all lens', () => {
    expect(testIssues.every((issue) => inLens(issue, 'all'))).toBe(true)
  })
})

describe('useIssuesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('reads every unclosed issue by sending no status at all', async () => {
    mockApi.get.mockResolvedValueOnce({ data: testIssues })
    const store = useIssuesStore()
    await store.fetchAll()
    expect(mockApi.get).toHaveBeenCalledWith('/issues/', { params: {} })
    expect(store.items).toHaveLength(5)
  })

  it('sends each filter under the parameter name the API takes', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    store.setFilters({ status: 'all', repo: 'dotfiles', type: 'bug', label: 'area-cli', initiative: 'Ship it', priority: '1' })
    store.search = '  router  '
    await store.fetchAll()
    expect(mockApi.get).toHaveBeenCalledWith('/issues/', {
      params: { status: 'all', repo: 'dotfiles', type: 'bug', label: 'area-cli', initiative: 'Ship it', priority: 1, search: 'router' },
    })
  })

  // The API reads `repo=''` as the issues on no repo. Dropped by a truthiness
  // check, it would become no filter and return every repo's issues.
  it('sends an empty repo for the issues that name none', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    await store.setFilter('repo', '')
    expect(mockApi.get).toHaveBeenCalledWith('/issues/', { params: { repo: '' } })
  })

  it('counts each lens from the loaded rows', async () => {
    mockApi.get.mockResolvedValueOnce({ data: testIssues })
    const store = useIssuesStore()
    await store.fetchAll()
    expect(store.lensCounts).toEqual({ all: 5, ready: 1, in_progress: 1, blocked: 1, triage: 1, decisions: 1 })
  })

  it('narrows the rows to the lens without reading again', async () => {
    mockApi.get.mockResolvedValueOnce({ data: testIssues })
    const store = useIssuesStore()
    await store.fetchAll()
    store.setLens('decisions')
    expect(store.visibleItems.map((issue) => issue.number)).toEqual([14])
    expect(mockApi.get).toHaveBeenCalledOnce()
  })

  it('keeps the repo choices while a repo filter narrows the rows', async () => {
    mockApi.get.mockResolvedValueOnce({ data: [ready, makeIssue({ number: 20, repo: 'dotfiles' }), makeIssue({ number: 21, repo: null })] })
    const store = useIssuesStore()
    await store.fetchAll()
    expect(store.knownRepos).toEqual(['dotfiles', 'ichrisbirch'])

    mockApi.get.mockResolvedValueOnce({ data: [ready] })
    await store.setFilter('repo', 'ichrisbirch')
    expect(store.knownRepos).toEqual(['dotfiles', 'ichrisbirch'])
  })

  it('names every narrowing in force, the lens included', () => {
    const store = useIssuesStore()
    store.vocabulary = testVocabulary
    store.setFilters({ repo: '', priority: '1', label: 'area-cli' })
    store.setLens('blocked')
    expect(store.activeFilters).toEqual(['no repo', 'label area-cli', 'priority urgent', 'blocked'])
  })

  it('resets every filter and the lens', () => {
    const store = useIssuesStore()
    store.setFilters({ status: 'all', repo: 'dotfiles', label: 'area-cli' })
    store.search = 'router'
    store.setLens('triage')
    store.resetFilters()
    expect(store.filters()).toEqual({})
    expect(store.lens).toBe('all')
  })

  it('opens one issue at a time and closes it on a second toggle', async () => {
    mockApi.get.mockResolvedValue({ data: detailOf(ready) })
    const store = useIssuesStore()
    await store.toggleDetail(ready)
    expect(mockApi.get).toHaveBeenCalledWith('/issues/10/')
    expect(store.expandedId).toBe(ready.id)
    expect(store.detail?.number).toBe(10)

    await store.toggleDetail(ready)
    expect(store.expandedId).toBeNull()
    expect(store.detail).toBeNull()
  })

  // Completing one issue can unblock another and move inherited priority, so a
  // one-row patch would leave the other rows' flags and priorities stale.
  it('reads the list again after a write', async () => {
    mockApi.patch.mockResolvedValueOnce({ data: detailOf({ ...ready, status: 'completed' }) })
    mockApi.get.mockImplementation(async (url: string) => ({ data: url === '/issues/vocabulary/' ? testVocabulary : [blocked] }))
    const store = useIssuesStore()
    store.items = testIssues
    await store.setStatus(ready, 'completed')
    expect(mockApi.patch).toHaveBeenCalledWith('/issues/10/', { status: 'completed' })
    expect(store.items.map((issue) => issue.number)).toEqual([12])
  })

  it('sends a cancel with its reason in one request', async () => {
    mockApi.patch.mockResolvedValueOnce({ data: detailOf(ready) })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    await store.setStatus(ready, 'canceled', { status_reason: 'Covered elsewhere' })
    expect(mockApi.patch).toHaveBeenCalledWith('/issues/10/', { status_reason: 'Covered elsewhere', status: 'canceled' })
  })

  it('re-reads an open detail after a write so its comments stay current', async () => {
    mockApi.get.mockImplementation(async (url: string) => {
      if (url === '/issues/vocabulary/') return { data: testVocabulary }
      if (url === '/issues/10/') return { data: detailOf(ready) }
      return { data: testIssues }
    })
    mockApi.post.mockResolvedValueOnce({
      data: { id: 'c1', issue_id: ready.id, body: 'Found it', author: 'Chris', created_ts: '2026-10-07T12:00:00Z' },
    })
    const store = useIssuesStore()
    store.items = testIssues
    await store.toggleDetail(ready)
    mockApi.get.mockClear()

    await store.addComment(ready, 'Found it', 'Chris')
    expect(mockApi.post).toHaveBeenCalledWith('/issues/10/comments/', { body: 'Found it', author: 'Chris' })
    expect(mockApi.get).toHaveBeenCalledWith('/issues/10/')
  })

  it('closes the detail of an issue it deletes', async () => {
    mockApi.get.mockImplementation(async (url: string) => ({ data: url === '/issues/10/' ? detailOf(ready) : [] }))
    mockApi.delete.mockResolvedValueOnce({ data: null })
    const store = useIssuesStore()
    await store.toggleDetail(ready)
    await store.remove(ready)
    expect(mockApi.delete).toHaveBeenCalledWith('/issues/10/')
    expect(store.expandedId).toBeNull()
  })

  it('names both issues in the path that removes a dependency', async () => {
    mockApi.delete.mockResolvedValueOnce({ data: null })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    await store.removeDependency(blocked, blocked.depends_on[0]!)
    expect(mockApi.delete).toHaveBeenCalledWith('/issues/12/dependencies/10/')
  })

  it('places an issue beside a neighbor through the rank endpoint', async () => {
    mockApi.post.mockResolvedValueOnce({ data: ready })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    await store.move(ready, { before: 14 })
    expect(mockApi.post).toHaveBeenCalledWith('/issues/10/rank/', { before: 14 })
  })

  it('releases a claim with a DELETE on the claim', async () => {
    mockApi.delete.mockResolvedValueOnce({ data: claimed })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssuesStore()
    await store.release(claimed)
    expect(mockApi.delete).toHaveBeenCalledWith('/issues/11/claim/')
  })

  it('surfaces a refused write as an ApiError and reads nothing after it', async () => {
    const refusal = new ApiError({ message: '#10 still has open children', detail: '#10 still has open children', status: 409 })
    mockApi.patch.mockRejectedValueOnce(refusal)
    const store = useIssuesStore()
    await expect(store.setStatus(ready, 'completed')).rejects.toBe(refusal)
    expect(store.error).toBe(refusal)
    expect(mockApi.get).not.toHaveBeenCalled()
  })

  it('reports the write as done when only the re-read after it fails', async () => {
    mockApi.post.mockResolvedValueOnce({ data: detailOf(ready) })
    mockApi.get.mockRejectedValue(new ApiError({ message: 'down', detail: 'down', status: 503 }))
    const store = useIssuesStore()
    await expect(store.create({ title: 'Ready task' })).resolves.toMatchObject({ number: 10 })
  })
})
