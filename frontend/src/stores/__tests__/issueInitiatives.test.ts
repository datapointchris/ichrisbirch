import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIssueInitiativesStore } from '../issueInitiatives'
import { ApiError } from '@/api/errors'
import type { Initiative } from '@/api/client'

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

const initiative: Initiative = {
  id: 'init-1',
  name: 'Ship the tracker',
  description: null,
  status: 'active',
  status_reason: null,
  priority: 2,
  position: 0,
  created_ts: '2026-10-01T12:00:00Z',
  closed_ts: null,
  issue_count: 3,
  open_count: 1,
  completed_count: 1,
  canceled_count: 1,
  repos: ['ichrisbirch'],
}

describe('useIssueInitiativesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('reads the active initiatives unless another status is asked for', async () => {
    mockApi.get.mockResolvedValue({ data: [initiative] })
    const store = useIssueInitiativesStore()
    await store.fetchAll()
    expect(mockApi.get).toHaveBeenCalledWith('/issues/initiatives/', { params: { status: 'active' } })

    await store.setStatusFilter('all')
    expect(mockApi.get).toHaveBeenLastCalledWith('/issues/initiatives/', { params: { status: 'all' } })
  })

  it('drops an initiative with its reason and reads the list again', async () => {
    mockApi.patch.mockResolvedValueOnce({ data: { ...initiative, status: 'dropped' } })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssueInitiativesStore()
    await store.setStatus(initiative, 'dropped', 'Superseded')
    expect(mockApi.patch).toHaveBeenCalledWith('/issues/initiatives/init-1/', { status: 'dropped', status_reason: 'Superseded' })
    expect(mockApi.get).toHaveBeenCalledOnce()
  })

  it('completes an initiative without inventing a reason', async () => {
    mockApi.patch.mockResolvedValueOnce({ data: { ...initiative, status: 'completed' } })
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useIssueInitiativesStore()
    await store.setStatus(initiative, 'completed')
    expect(mockApi.patch).toHaveBeenCalledWith('/issues/initiatives/init-1/', { status: 'completed' })
  })

  it('surfaces a refused write and leaves the list alone', async () => {
    const refusal = new ApiError({ message: 'taken', detail: "An active initiative named 'Ship the tracker' already exists", status: 409 })
    mockApi.post.mockRejectedValueOnce(refusal)
    const store = useIssueInitiativesStore()
    await expect(store.create({ name: 'Ship the tracker' })).rejects.toBe(refusal)
    expect(store.error).toBe(refusal)
    expect(mockApi.get).not.toHaveBeenCalled()
  })
})
