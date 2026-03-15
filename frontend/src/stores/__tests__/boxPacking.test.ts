import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBoxPackingStore } from '../boxPacking'
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

const testItems = [
  { id: 10, box_id: 1, name: 'Plates', essential: true, warm: false, liquid: false },
  { id: 11, box_id: 1, name: 'Cups', essential: false, warm: false, liquid: false },
  { id: 12, box_id: 2, name: 'Jacket', essential: false, warm: true, liquid: false },
]

const testBoxes = [
  {
    id: 1,
    number: 3,
    name: 'Kitchen',
    size: 'Large' as const,
    essential: true,
    warm: false,
    liquid: false,
    items: [testItems[0]!, testItems[1]!],
  },
  { id: 2, number: 1, name: 'Clothes', size: 'Medium' as const, essential: false, warm: true, liquid: false, items: [testItems[2]!] },
  { id: 3, number: 2, name: 'Empty', size: 'Small' as const, essential: false, warm: false, liquid: false, items: [] },
]

const testOrphans = [
  { id: 20, name: 'Lost Sock', essential: false, warm: true, liquid: false },
  { id: 21, name: 'Mystery Item', essential: false, warm: false, liquid: true },
]

describe('useBoxPackingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useBoxPackingStore()
    expect(store.boxes).toEqual([])
    expect(store.orphans).toEqual([])
    expect(store.searchResults).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.viewMode).toBe('block')
    expect(store.sortField1).toBe('number')
    expect(store.sortField2).toBe('')
  })

  // --- fetchBoxes ---

  it('fetches boxes from API', async () => {
    mockApi.get.mockResolvedValue({ data: testBoxes })
    const store = useBoxPackingStore()

    await store.fetchBoxes()

    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/boxes/')
    expect(store.boxes).toEqual(testBoxes)
    expect(store.loading).toBe(false)
  })

  it('sets loading state during fetch', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.get.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useBoxPackingStore()

    const fetchPromise = store.fetchBoxes()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Server error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useBoxPackingStore()

    await expect(store.fetchBoxes()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- fetchBox ---

  it('fetches single box and updates in array', async () => {
    const updatedBox = { ...testBoxes[0]!, name: 'Updated Kitchen' }
    mockApi.get.mockResolvedValue({ data: updatedBox })
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    const result = await store.fetchBox(1)

    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/boxes/1/')
    expect(result).toEqual(updatedBox)
    expect(store.boxes.find((b) => b.id === 1)!.name).toBe('Updated Kitchen')
  })

  // --- createBox ---

  it('creates a box and adds to list', async () => {
    const newBox = { id: 4, number: 4, name: 'Books', size: 'Book' as const, essential: false, warm: false, liquid: false, items: [] }
    mockApi.post.mockResolvedValue({ data: newBox })
    const store = useBoxPackingStore()

    const result = await store.createBox({ name: 'Books', number: 4, size: 'Book', essential: false, warm: false, liquid: false })

    expect(mockApi.post).toHaveBeenCalledWith('/box-packing/boxes/', expect.objectContaining({ name: 'Books' }))
    expect(result).toEqual(newBox)
    expect(store.boxes).toContainEqual(newBox)
  })

  it('sets error on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useBoxPackingStore()

    await expect(store.createBox({ name: 'Bad', size: 'Small', essential: false, warm: false, liquid: false })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.boxes).toEqual([])
  })

  // --- updateBox ---

  it('updates a box in place', async () => {
    const updated = { ...testBoxes[0]!, name: 'Updated Kitchen' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    const result = await store.updateBox(1, { name: 'Updated Kitchen' })

    expect(mockApi.patch).toHaveBeenCalledWith('/box-packing/boxes/1/', { name: 'Updated Kitchen' })
    expect(result).toEqual(updated)
    expect(store.boxes.find((b) => b.id === 1)!.name).toBe('Updated Kitchen')
  })

  // --- deleteBox ---

  it('removes a box from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    await store.deleteBox(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/box-packing/boxes/2/')
    expect(store.boxes).toHaveLength(2)
    expect(store.boxes.find((b) => b.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'DB error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    await expect(store.deleteBox(1)).rejects.toThrow(ApiError)
    expect(store.boxes).toHaveLength(3)
  })

  // --- createItem ---

  it('creates an item and re-fetches parent box', async () => {
    const newItem = { id: 13, box_id: 1, name: 'Bowls', essential: false, warm: false, liquid: false }
    const updatedBox = { ...testBoxes[0]!, items: [...testBoxes[0]!.items, newItem] }
    mockApi.post.mockResolvedValue({ data: newItem })
    mockApi.get.mockResolvedValue({ data: updatedBox })
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    await store.createItem({ box_id: 1, name: 'Bowls', essential: false, warm: false, liquid: false })

    expect(mockApi.post).toHaveBeenCalledWith('/box-packing/items/', expect.objectContaining({ name: 'Bowls' }))
    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/boxes/1/')
  })

  // --- deleteItem ---

  it('deletes an item and re-fetches parent box', async () => {
    mockApi.delete.mockResolvedValue({})
    mockApi.get.mockResolvedValue({ data: { ...testBoxes[0]!, items: [testItems[1]!] } })
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    await store.deleteItem(10, 1)

    expect(mockApi.delete).toHaveBeenCalledWith('/box-packing/items/10/')
    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/boxes/1/')
  })

  // --- orphanItem ---

  it('orphans an item by patching box_id to null', async () => {
    mockApi.patch.mockResolvedValue({ data: { ...testItems[0]!, box_id: null } })
    mockApi.get.mockResolvedValue({ data: { ...testBoxes[0]!, items: [testItems[1]!] } })
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]

    await store.orphanItem(10, 1)

    expect(mockApi.patch).toHaveBeenCalledWith('/box-packing/items/10/', { box_id: null })
    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/boxes/1/')
  })

  // --- assignOrphanToBox ---

  it('assigns an orphan to a box and removes from orphans list', async () => {
    mockApi.patch.mockResolvedValue({ data: { ...testOrphans[0]!, box_id: 1 } })
    mockApi.get.mockResolvedValue({ data: testBoxes[0] })
    const store = useBoxPackingStore()
    store.orphans = [...testOrphans]
    store.boxes = [...testBoxes]

    await store.assignOrphanToBox(20, 1)

    expect(mockApi.patch).toHaveBeenCalledWith('/box-packing/items/20/', { box_id: 1 })
    expect(store.orphans.find((o) => o.id === 20)).toBeUndefined()
  })

  // --- fetchOrphans ---

  it('fetches orphaned items', async () => {
    mockApi.get.mockResolvedValue({ data: testOrphans })
    const store = useBoxPackingStore()

    await store.fetchOrphans()

    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/items/orphans/')
    expect(store.orphans).toEqual(testOrphans)
  })

  // --- deleteOrphan ---

  it('deletes an orphan from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useBoxPackingStore()
    store.orphans = [...testOrphans]

    await store.deleteOrphan(20)

    expect(mockApi.delete).toHaveBeenCalledWith('/box-packing/items/20/')
    expect(store.orphans).toHaveLength(1)
    expect(store.orphans.find((o) => o.id === 20)).toBeUndefined()
  })

  // --- search ---

  it('maps search tuple response to BoxSearchResult objects', async () => {
    const tupleResponse = [
      [testBoxes[0], testItems[0]],
      [testBoxes[0], testItems[1]],
    ]
    mockApi.get.mockResolvedValue({ data: tupleResponse })
    const store = useBoxPackingStore()

    await store.search('plate')

    expect(mockApi.get).toHaveBeenCalledWith('/box-packing/search/', { params: { q: 'plate' } })
    expect(store.searchResults).toHaveLength(2)
    expect(store.searchResults[0]!.box).toEqual(testBoxes[0])
    expect(store.searchResults[0]!.item).toEqual(testItems[0])
  })

  // --- sortedBoxes ---

  it('sorts boxes by number ascending (default)', () => {
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]
    const sorted = store.sortedBoxes
    expect(sorted[0]!.name).toBe('Clothes') // number 1
    expect(sorted[1]!.name).toBe('Empty') // number 2
    expect(sorted[2]!.name).toBe('Kitchen') // number 3
  })

  it('sorts by name when sortField1 is name', () => {
    const store = useBoxPackingStore()
    store.boxes = [...testBoxes]
    store.sortField1 = 'name'
    const sorted = store.sortedBoxes
    expect(sorted[0]!.name).toBe('Clothes')
    expect(sorted[1]!.name).toBe('Empty')
    expect(sorted[2]!.name).toBe('Kitchen')
  })

  it('uses secondary sort when primary values are equal', () => {
    const store = useBoxPackingStore()
    store.boxes = [
      { id: 1, number: 1, name: 'B Box', size: 'Small' as const, essential: false, warm: false, liquid: false, items: [] },
      { id: 2, number: 1, name: 'A Box', size: 'Small' as const, essential: false, warm: false, liquid: false, items: [] },
    ]
    store.sortField1 = 'number'
    store.sortField2 = 'name'
    const sorted = store.sortedBoxes
    expect(sorted[0]!.name).toBe('A Box')
    expect(sorted[1]!.name).toBe('B Box')
  })

  // --- viewMode ---

  it('persists viewMode to localStorage', () => {
    const store = useBoxPackingStore()
    store.setViewMode('compact')
    expect(store.viewMode).toBe('compact')
    expect(localStorage.getItem('boxPacking.viewMode')).toBe('compact')
  })

  it('reads viewMode from localStorage on init', () => {
    localStorage.setItem('boxPacking.viewMode', 'compact')
    const store = useBoxPackingStore()
    expect(store.viewMode).toBe('compact')
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useBoxPackingStore()
    store.error = new ApiError({ message: 'err', detail: 'err' }) as typeof store.error
    store.clearError()
    expect(store.error).toBeNull()
  })

  // --- network error ---

  it('handles network errors with structured ApiError', async () => {
    const networkError = new ApiError({
      message: 'Network error',
      detail: 'Unable to reach the server.',
      isNetworkError: true,
    })
    mockApi.get.mockRejectedValue(networkError)
    const store = useBoxPackingStore()

    await expect(store.fetchBoxes()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
  })
})
