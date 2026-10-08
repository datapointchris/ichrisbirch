import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIssueLabelsStore } from '../issueLabels'
import type { IssueLabel } from '@/api/client'

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

const labels: IssueLabel[] = [
  { slug: 'area-cli', group_slug: 'area', description: null, open_issue_count: 2 },
  { slug: 'area-api', group_slug: 'area', description: null, open_issue_count: 0 },
  { slug: 'size-s', group_slug: 'size', description: null, open_issue_count: 1 },
  { slug: 'needs-design', group_slug: null, description: 'Waiting on a design call', open_issue_count: 1 },
]

describe('useIssueLabelsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('names each group in use once', async () => {
    mockApi.get.mockResolvedValueOnce({ data: labels })
    const store = useIssueLabelsStore()
    await store.fetchAll()
    expect(store.groups).toEqual(['area', 'size'])
  })

  it('addresses a label by its slug, which never changes', async () => {
    mockApi.patch.mockResolvedValueOnce({ data: labels[0] })
    mockApi.delete.mockResolvedValueOnce({ data: null })
    mockApi.get.mockResolvedValue({ data: labels })
    const store = useIssueLabelsStore()
    await store.update('area-cli', { group_slug: null })
    await store.remove('area-cli')
    expect(mockApi.patch).toHaveBeenCalledWith('/issues/labels/area-cli/', { group_slug: null })
    expect(mockApi.delete).toHaveBeenCalledWith('/issues/labels/area-cli/')
  })
})
