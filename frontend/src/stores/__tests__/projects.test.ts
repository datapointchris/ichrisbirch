import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectsStore } from '../projects'
import { ApiError } from '@/api/errors'

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

const testProjects = [
  { id: 1, name: 'Music Setup', position: 0, created_at: '2026-01-01T00:00:00Z', item_count: 3 },
  { id: 2, name: 'Home Renovation', position: 1, created_at: '2026-02-01T00:00:00Z', item_count: 2 },
  { id: 3, name: 'Career Goals', position: 2, created_at: '2026-03-01T00:00:00Z', item_count: 0 },
]

const testItems = [
  {
    id: 10,
    title: 'Decide budget',
    notes: 'Check forums',
    completed: false,
    archived: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    position: 0,
  },
  {
    id: 11,
    title: 'Research interfaces',
    notes: null,
    completed: false,
    archived: false,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    position: 1,
  },
  {
    id: 12,
    title: 'Buy interface',
    notes: 'Wait for sale',
    completed: true,
    archived: false,
    created_at: '2026-01-03T00:00:00Z',
    updated_at: '2026-01-03T00:00:00Z',
    position: 2,
  },
]

const testItemDetail = {
  id: 10,
  title: 'Decide budget',
  notes: 'Check forums',
  completed: false,
  archived: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  projects: [{ id: 1, name: 'Music Setup', position: 0, created_at: '2026-01-01T00:00:00Z' }],
  dependency_ids: [11],
}

describe('useProjectsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // Default: blocker fetches return empty (most tests don't need blockers)
    mockApi.get.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/blockers/')) {
        return Promise.resolve({ data: [] })
      }
      return Promise.resolve({ data: [] })
    })
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useProjectsStore()
    expect(store.projects).toEqual([])
    expect(store.items).toEqual([])
    expect(store.selectedProjectId).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.itemsLoading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.itemBlockers).toEqual({})
  })

  // --- fetchProjects ---

  it('fetches projects and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testProjects })
    const store = useProjectsStore()

    await store.fetchProjects()

    expect(mockApi.get).toHaveBeenCalledWith('/projects/')
    expect(store.projects).toEqual(testProjects)
    expect(store.loading).toBe(false)
  })

  it('sets loading during fetch', async () => {
    let resolve!: (v: unknown) => void
    mockApi.get.mockReturnValue(new Promise((r) => (resolve = r)))
    const store = useProjectsStore()

    const p = store.fetchProjects()
    expect(store.loading).toBe(true)

    resolve({ data: [] })
    await p
    expect(store.loading).toBe(false)
  })

  it('sets error on fetch failure', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Server error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- createProject ---

  it('creates a project and refetches', async () => {
    mockApi.post.mockResolvedValue({ data: { id: 4, name: 'New', position: 3 } })
    mockApi.get.mockResolvedValue({ data: [...testProjects] })
    const store = useProjectsStore()

    await store.createProject({ name: 'New' })

    expect(mockApi.post).toHaveBeenCalledWith('/projects/', { name: 'New' })
    expect(mockApi.get).toHaveBeenCalledWith('/projects/')
  })

  it('sets error on create failure', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Duplicate name', status: 409 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useProjectsStore()

    await expect(store.createProject({ name: 'Dup' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- updateProject ---

  it('updates a project and refetches', async () => {
    mockApi.patch.mockResolvedValue({ data: { id: 1, name: 'Renamed', position: 0 } })
    mockApi.get.mockResolvedValue({ data: testProjects })
    const store = useProjectsStore()

    await store.updateProject(1, { name: 'Renamed' })

    expect(mockApi.patch).toHaveBeenCalledWith('/projects/1/', { name: 'Renamed' })
  })

  // --- removeProject ---

  it('removes a project from local state', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useProjectsStore()
    store.projects = [...testProjects]

    await store.removeProject(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/projects/2/')
    expect(store.projects).toHaveLength(2)
    expect(store.projects.find((p) => p.id === 2)).toBeUndefined()
  })

  it('clears selection when removing selected project', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useProjectsStore()
    store.projects = [...testProjects]
    store.selectedProjectId = 2
    store.items = [...testItems]

    await store.removeProject(2)

    expect(store.selectedProjectId).toBeNull()
    expect(store.items).toEqual([])
  })

  it('sets error on remove failure', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Has orphan items', status: 409 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useProjectsStore()
    store.projects = [...testProjects]

    await expect(store.removeProject(1)).rejects.toThrow(ApiError)
    expect(store.projects).toHaveLength(3)
  })

  // --- sortedProjects ---

  it('sorts projects by position', () => {
    const store = useProjectsStore()
    store.projects = [testProjects[2]!, testProjects[0]!, testProjects[1]!]

    expect(store.sortedProjects[0]!.name).toBe('Music Setup')
    expect(store.sortedProjects[1]!.name).toBe('Home Renovation')
    expect(store.sortedProjects[2]!.name).toBe('Career Goals')
  })

  // --- selectedProject ---

  it('returns null when no project selected', () => {
    const store = useProjectsStore()
    expect(store.selectedProject).toBeNull()
  })

  it('returns the selected project', () => {
    const store = useProjectsStore()
    store.projects = [...testProjects]
    store.selectedProjectId = 2

    expect(store.selectedProject!.name).toBe('Home Renovation')
  })

  // --- fetchItems ---

  it('fetches items for a project and sets state', async () => {
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/projects/1/items/') return Promise.resolve({ data: testItems })
      return Promise.resolve({ data: [] })
    })
    const store = useProjectsStore()

    await store.fetchItems(1)

    expect(store.selectedProjectId).toBe(1)
    expect(store.items).toEqual(testItems)
    expect(store.itemsLoading).toBe(false)
  })

  it('clears blockers when fetching new items', async () => {
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/projects/1/items/') return Promise.resolve({ data: testItems })
      return Promise.resolve({ data: [] })
    })
    const store = useProjectsStore()
    store.itemBlockers = { 99: [{ id: 98, title: 'old', completed: false, archived: false, created_at: '', updated_at: '' }] }

    await store.fetchItems(1)

    // itemBlockers was cleared at start (then refilled by fetchItemBlockers)
    // Since our mock returns empty blockers, it should be empty
    expect(store.itemBlockers).toEqual({})
  })

  it('sets error on items fetch failure', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Not found', status: 404 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useProjectsStore()

    await expect(store.fetchItems(999)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.itemsLoading).toBe(false)
  })

  // --- sortedItems ---

  it('sorts items by position', () => {
    const store = useProjectsStore()
    store.items = [testItems[2]!, testItems[0]!, testItems[1]!]

    expect(store.sortedItems[0]!.title).toBe('Decide budget')
    expect(store.sortedItems[1]!.title).toBe('Research interfaces')
    expect(store.sortedItems[2]!.title).toBe('Buy interface')
  })

  // --- createItem ---

  it('creates an item and refetches projects and items', async () => {
    const newItemDetail = { ...testItemDetail, id: 20, title: 'New item', dependency_ids: [], projects: [] }
    mockApi.post.mockResolvedValue({ data: newItemDetail })
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/projects/') return Promise.resolve({ data: testProjects })
      if (url === '/projects/1/items/') return Promise.resolve({ data: testItems })
      return Promise.resolve({ data: [] })
    })
    const store = useProjectsStore()
    store.selectedProjectId = 1

    const result = await store.createItem({ title: 'New item', project_ids: [1] })

    expect(mockApi.post).toHaveBeenCalledWith('/project-items/', { title: 'New item', project_ids: [1] })
    expect(result.id).toBe(20)
  })

  // --- updateItem ---

  it('updates an item in place preserving position', async () => {
    const updatedItem = {
      id: 10,
      title: 'Updated',
      notes: 'New',
      completed: false,
      archived: false,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    }
    mockApi.patch.mockResolvedValue({ data: updatedItem })
    const store = useProjectsStore()
    store.items = [...testItems]

    await store.updateItem(10, { title: 'Updated', notes: 'New' })

    expect(mockApi.patch).toHaveBeenCalledWith('/project-items/10/', { title: 'Updated', notes: 'New' })
    const item = store.items.find((i) => i.id === 10)
    expect(item!.title).toBe('Updated')
    expect(item!.position).toBe(0) // position preserved from original
  })

  // --- removeItem ---

  it('removes an item and refetches projects', async () => {
    mockApi.delete.mockResolvedValue({})
    mockApi.get.mockResolvedValue({ data: testProjects })
    const store = useProjectsStore()
    store.items = [...testItems]

    await store.removeItem(11)

    expect(mockApi.delete).toHaveBeenCalledWith('/project-items/11/')
    expect(store.items).toHaveLength(2)
    expect(store.items.find((i) => i.id === 11)).toBeUndefined()
  })

  // --- reorderItems ---

  it('sends position updates only for items that moved', async () => {
    mockApi.patch.mockResolvedValue({ data: {} })
    const store = useProjectsStore()
    store.selectedProjectId = 1
    store.items = [...testItems] // positions: 0, 1, 2

    // Reorder: swap first two items
    await store.reorderItems([11, 10, 12])

    // Item 10 moved from position 0 → 1, item 11 from 1 → 0
    // Item 12 stays at position 2 (no call)
    expect(mockApi.patch).toHaveBeenCalledTimes(2)
    expect(mockApi.patch).toHaveBeenCalledWith('/project-items/11/reorder/', { project_id: 1, position: 0 })
    expect(mockApi.patch).toHaveBeenCalledWith('/project-items/10/reorder/', { project_id: 1, position: 1 })
  })

  it('does nothing when no project is selected', async () => {
    const store = useProjectsStore()
    store.selectedProjectId = null

    await store.reorderItems([11, 10])

    expect(mockApi.patch).not.toHaveBeenCalled()
  })

  // --- reorderProjects ---

  it('sends position updates for moved projects', async () => {
    mockApi.patch.mockResolvedValue({ data: {} })
    const store = useProjectsStore()
    store.projects = [...testProjects]

    await store.reorderProjects([3, 1, 2])

    expect(mockApi.patch).toHaveBeenCalledWith('/projects/3/', { position: 0 })
    expect(mockApi.patch).toHaveBeenCalledWith('/projects/1/', { position: 1 })
    expect(mockApi.patch).toHaveBeenCalledWith('/projects/2/', { position: 2 })
  })

  // --- completeItem / archiveItem ---

  it('completeItem calls updateItem with completed: true', async () => {
    const updatedItem = { ...testItems[0], completed: true }
    mockApi.patch.mockResolvedValue({ data: updatedItem })
    const store = useProjectsStore()
    store.items = [...testItems]

    await store.completeItem(10)

    expect(mockApi.patch).toHaveBeenCalledWith('/project-items/10/', { completed: true })
  })

  it('archiveItem calls updateItem with archived: true', async () => {
    const updatedItem = { ...testItems[0], archived: true }
    mockApi.patch.mockResolvedValue({ data: updatedItem })
    const store = useProjectsStore()
    store.items = [...testItems]

    await store.archiveItem(10)

    expect(mockApi.patch).toHaveBeenCalledWith('/project-items/10/', { archived: true })
  })

  // --- fetchItemBlockers ---

  it('fetches blockers for all items in project', async () => {
    const blockerItem = { id: 10, title: 'Decide budget', completed: false, archived: false, created_at: '', updated_at: '' }
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/project-items/11/blockers/') return Promise.resolve({ data: [blockerItem] })
      if (url.includes('/blockers/')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })
    const store = useProjectsStore()
    store.items = [...testItems]

    await store.fetchItemBlockers()

    expect(store.itemBlockers[11]).toEqual([blockerItem])
    expect(store.itemBlockers[10]).toBeUndefined()
    expect(store.itemBlockers[12]).toBeUndefined()
  })

  // --- fetchItemDetail ---

  it('fetches item detail with projects and dependencies', async () => {
    mockApi.get.mockResolvedValue({ data: testItemDetail })
    const store = useProjectsStore()

    const result = await store.fetchItemDetail(10)

    expect(mockApi.get).toHaveBeenCalledWith('/project-items/10/')
    expect(result.projects).toHaveLength(1)
    expect(result.dependency_ids).toEqual([11])
  })

  // --- addDependency ---

  it('adds a dependency and returns updated detail', async () => {
    const updatedDetail = { ...testItemDetail, dependency_ids: [11, 12] }
    mockApi.post.mockResolvedValue({ data: updatedDetail })
    const store = useProjectsStore()

    const result = await store.addDependency(10, { depends_on_id: 12 })

    expect(mockApi.post).toHaveBeenCalledWith('/project-items/10/dependencies/', { depends_on_id: 12 })
    expect(result.dependency_ids).toEqual([11, 12])
  })

  it('sets error on cycle detection', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Would create cycle', status: 409 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useProjectsStore()

    await expect(store.addDependency(10, { depends_on_id: 11 })).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(409)
  })

  // --- removeDependency ---

  it('removes a dependency', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useProjectsStore()

    await store.removeDependency(10, 11)

    expect(mockApi.delete).toHaveBeenCalledWith('/project-items/10/dependencies/11/')
  })

  // --- addToProject / removeFromProject ---

  it('adds item to project and refetches projects', async () => {
    mockApi.post.mockResolvedValue({ data: { id: 2, name: 'Home Renovation', position: 1, created_at: '' } })
    mockApi.get.mockResolvedValue({ data: testProjects })
    const store = useProjectsStore()

    await store.addToProject(10, { project_id: 2 })

    expect(mockApi.post).toHaveBeenCalledWith('/project-items/10/projects/', { project_id: 2 })
    expect(mockApi.get).toHaveBeenCalledWith('/projects/')
  })

  it('removes item from project and refetches', async () => {
    mockApi.delete.mockResolvedValue({})
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/projects/') return Promise.resolve({ data: testProjects })
      if (url === '/projects/1/items/') return Promise.resolve({ data: testItems })
      return Promise.resolve({ data: [] })
    })
    const store = useProjectsStore()
    store.selectedProjectId = 1

    await store.removeFromProject(10, 2)

    expect(mockApi.delete).toHaveBeenCalledWith('/project-items/10/projects/2/')
  })

  it('sets error when removing from last project', async () => {
    const apiError = new ApiError({ message: 'fail', detail: 'Cannot remove from last project', status: 409 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useProjectsStore()

    await expect(store.removeFromProject(10, 1)).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(409)
  })

  // --- searchItems ---

  it('searches items across all projects', async () => {
    const results = [testItems[0]!, testItems[1]!]
    mockApi.get.mockResolvedValue({ data: results })
    const store = useProjectsStore()

    const result = await store.searchItems('budget')

    expect(mockApi.get).toHaveBeenCalledWith('/project-items/search/', { params: { q: 'budget' } })
    expect(result).toHaveLength(2)
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useProjectsStore()
    store.error = new ApiError({ message: 'err', detail: 'err' }) as typeof store.error
    store.clearError()
    expect(store.error).toBeNull()
  })

  // --- network error ---

  it('handles network errors with structured ApiError', async () => {
    const networkError = new ApiError({
      message: 'Network error',
      detail: 'Unable to reach the server. Check your connection.',
      isNetworkError: true,
    })
    mockApi.get.mockRejectedValue(networkError)
    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
