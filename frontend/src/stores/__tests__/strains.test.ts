import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useStrainsStore, humanizeStrainValue } from '../strains'
import { ApiError } from '@/api/errors'
import type { Strain, StrainVocabulary } from '@/api/client'

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

// Covers both status values, a rated and an unrated strain, and one row whose
// optional fields are all absent.
const testStrains: Strain[] = [
  {
    id: 1,
    name: 'Blue Dream',
    breeder: 'Humboldt Seed Company',
    lineage: 'Blueberry x Haze',
    strain_type: 'sativa_dominant',
    status: 'tried',
    thc_percent: 18,
    cbd_percent: 0.1,
    rating: 8,
    effects: ['creative', 'relaxed'],
    flavors: ['berry'],
    terpenes: ['myrcene'],
    tags: ['daytime'],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Granddaddy Purple',
    strain_type: 'indica',
    status: 'tried',
    thc_percent: 20.5,
    rating: 3,
    effects: ['relaxed', 'sleepy'],
    flavors: ['grape'],
    terpenes: [],
    tags: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 3,
    name: 'Runtz',
    status: 'want_to_try',
    effects: [],
    flavors: [],
    terpenes: [],
    tags: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const testVocabulary: StrainVocabulary = {
  strain_type: [
    { name: 'indica', count: 1 },
    { name: 'sativa_dominant', count: 1 },
    { name: 'hybrid', count: 0 },
  ],
  status: [
    { name: 'tried', count: 2 },
    { name: 'want_to_try', count: 1 },
  ],
  effects: [
    { name: 'creative', count: 1 },
    { name: 'relaxed', count: 2 },
    { name: 'sleepy', count: 1 },
    { name: 'giggly', count: 0 },
  ],
  flavors: [{ name: 'berry', count: 1 }],
  terpenes: [{ name: 'myrcene', count: 1 }],
}

describe('humanizeStrainValue', () => {
  it('turns an underscored key into words', () => {
    expect(humanizeStrainValue('sativa_dominant')).toBe('Sativa Dominant')
    expect(humanizeStrainValue('indica')).toBe('Indica')
  })

  it('uppercases an acronym rather than title-casing it', () => {
    expect(humanizeStrainValue('cbd')).toBe('CBD')
    expect(humanizeStrainValue('thc')).toBe('THC')
  })

  it('renders an absent value as an empty string', () => {
    expect(humanizeStrainValue(undefined)).toBe('')
    expect(humanizeStrainValue('')).toBe('')
  })
})

describe('useStrainsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const store = useStrainsStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.sortField).toBe('name')
    expect(store.sortDirection).toBe('asc')
    expect(store.statusFilter).toBe('all')
    expect(store.typeFilter).toBe('all')
    expect(store.effectFilter).toBe('all')
  })

  it('starts with an empty vocabulary so the view renders before the fetch lands', () => {
    const store = useStrainsStore()
    expect(store.vocabulary.effects).toEqual([])
    expect(store.vocabulary.strain_type).toEqual([])
  })

  it('fetches strains from the API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testStrains })
    const store = useStrainsStore()
    await store.fetchAll()
    expect(mockApi.get).toHaveBeenCalledWith('/strains/', { params: {} })
    expect(store.items).toEqual(testStrains)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sets loading state during fetch', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.get.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useStrainsStore()
    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)
    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useStrainsStore()
    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears a previous error on a successful fetch', async () => {
    const store = useStrainsStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error
    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  it('fetches the vocabulary from its own endpoint', async () => {
    mockApi.get.mockResolvedValue({ data: testVocabulary })
    const store = useStrainsStore()
    await store.fetchVocabulary()
    expect(mockApi.get).toHaveBeenCalledWith('/strains/vocabulary/')
    expect(store.vocabulary.effects).toHaveLength(4)
  })

  it('keeps a vocabulary value nothing uses, so it can still be chosen', async () => {
    mockApi.get.mockResolvedValue({ data: testVocabulary })
    const store = useStrainsStore()
    await store.fetchVocabulary()
    const giggly = store.vocabulary.effects.find((e) => e.name === 'giggly')
    expect(giggly).toBeDefined()
    expect(giggly!.count).toBe(0)
  })

  describe('statusCounts', () => {
    it('counts from the vocabulary, not from the loaded rows', async () => {
      // The rows are a filtered page, so counting them would make each counter
      // report the narrowing rather than the catalog.
      mockApi.get.mockResolvedValue({ data: testVocabulary })
      const store = useStrainsStore()
      await store.fetchVocabulary()
      expect(store.statusCounts).toEqual({ tried: 2, want_to_try: 1, total: 3 })
    })

    it('holds steady while a filter narrows the rows', async () => {
      mockApi.get.mockResolvedValue({ data: testVocabulary })
      const store = useStrainsStore()
      await store.fetchVocabulary()

      mockApi.get.mockResolvedValue({ data: [testStrains[2]!] })
      await store.setStatusFilter('want_to_try')

      expect(store.items).toHaveLength(1)
      expect(store.statusCounts.total).toBe(3)
    })
  })

  describe('filtering is the server’s', () => {
    // One definition of each filter, in SQL, which is the one the CLI uses too.
    it('sends the status filter as a query parameter', async () => {
      mockApi.get.mockResolvedValue({ data: [] })
      const store = useStrainsStore()
      await store.setStatusFilter('want_to_try')
      expect(mockApi.get).toHaveBeenCalledWith('/strains/', { params: { status: 'want_to_try' } })
    })

    it('sends the type filter as a query parameter', async () => {
      mockApi.get.mockResolvedValue({ data: [] })
      const store = useStrainsStore()
      await store.setTypeFilter('indica')
      expect(mockApi.get).toHaveBeenCalledWith('/strains/', { params: { strain_type: 'indica' } })
    })

    it('sends the effect filter as a query parameter', async () => {
      mockApi.get.mockResolvedValue({ data: [] })
      const store = useStrainsStore()
      await store.setEffectFilter('relaxed')
      expect(mockApi.get).toHaveBeenCalledWith('/strains/', { params: { effect: 'relaxed' } })
    })

    it('sends every set filter together rather than the last one winning', async () => {
      mockApi.get.mockResolvedValue({ data: [] })
      const store = useStrainsStore()
      await store.setStatusFilter('tried')
      await store.setEffectFilter('sleepy')
      expect(store.filters()).toEqual({ status: 'tried', effect: 'sleepy' })
    })

    it('sends nothing when every filter is all', () => {
      const store = useStrainsStore()
      expect(store.filters()).toEqual({})
    })

    it('names the filters that narrowed an empty result', async () => {
      mockApi.get.mockResolvedValue({ data: [] })
      const store = useStrainsStore()
      await store.setStatusFilter('tried')
      await store.setEffectFilter('sleepy')
      expect(store.activeFilters).toEqual(['status tried', 'effect sleepy'])
    })
  })

  describe('sortedItems', () => {
    beforeEach(async () => {
      mockApi.get.mockResolvedValue({ data: testStrains })
      const store = useStrainsStore()
      await store.fetchAll()
    })

    it('sorts by name ascending by default', () => {
      const store = useStrainsStore()
      expect(store.sortedItems.map((s) => s.name)).toEqual(['Blue Dream', 'Granddaddy Purple', 'Runtz'])
    })

    it('reverses direction when the same field is set twice', () => {
      const store = useStrainsStore()
      store.setSort('name')
      expect(store.sortDirection).toBe('desc')
      expect(store.sortedItems.map((s) => s.name)).toEqual(['Runtz', 'Granddaddy Purple', 'Blue Dream'])
    })

    it('sorts an absent rating below every present one', () => {
      const store = useStrainsStore()
      store.setSort('rating')
      expect(store.sortedItems.map((s) => s.name)).toEqual(['Runtz', 'Granddaddy Purple', 'Blue Dream'])
    })
  })

  describe('mutations', () => {
    it('appends a created strain', async () => {
      const created = { ...testStrains[2]!, id: 9, name: 'MAC 1' }
      mockApi.post.mockResolvedValue({ data: created })
      mockApi.get.mockResolvedValue({ data: testVocabulary })
      const store = useStrainsStore()
      const result = await store.create({ name: 'MAC 1' })
      expect(mockApi.post).toHaveBeenCalledWith('/strains/', { name: 'MAC 1' })
      expect(result).toEqual(created)
      expect(store.items).toContainEqual(created)
    })

    describe('every write re-reads the counts', () => {
      // Each count on the page comes from the vocabulary, so a write that
      // changes one leaves the label stale until this runs.
      it('after a create', async () => {
        mockApi.post.mockResolvedValue({ data: testStrains[2] })
        mockApi.get.mockResolvedValue({ data: testVocabulary })
        const store = useStrainsStore()
        await store.create({ name: 'MAC 1' })
        expect(mockApi.get).toHaveBeenCalledWith('/strains/vocabulary/')
      })

      it('after an update', async () => {
        mockApi.patch.mockResolvedValue({ data: testStrains[0] })
        mockApi.get.mockResolvedValue({ data: testVocabulary })
        const store = useStrainsStore()
        await store.update(1, { rating: 10 })
        expect(mockApi.get).toHaveBeenCalledWith('/strains/vocabulary/')
      })

      it('after a delete', async () => {
        mockApi.delete.mockResolvedValue({ data: null })
        mockApi.get.mockResolvedValue({ data: testVocabulary })
        const store = useStrainsStore()
        await store.remove(1)
        expect(mockApi.get).toHaveBeenCalledWith('/strains/vocabulary/')
      })

      it('and a failed refresh does not fail the write', async () => {
        mockApi.post.mockResolvedValue({ data: testStrains[2] })
        mockApi.get.mockRejectedValue(new ApiError({ message: 'down', detail: 'down', status: 503 }))
        const store = useStrainsStore()
        await expect(store.create({ name: 'MAC 1' })).resolves.toBeTruthy()
      })
    })

    // `api.get` serves two paths here, because every write re-reads the counts.
    // One blanket mock would hand the vocabulary a list of strains.
    function routeGetByPath() {
      mockApi.get.mockImplementation((url: string) =>
        Promise.resolve({ data: url === '/strains/vocabulary/' ? testVocabulary : testStrains })
      )
    }

    it('replaces the updated strain in place', async () => {
      routeGetByPath()
      const store = useStrainsStore()
      await store.fetchAll()

      const updated = { ...testStrains[0]!, rating: 10 }
      mockApi.patch.mockResolvedValue({ data: updated })
      await store.update(1, { rating: 10 })
      expect(mockApi.patch).toHaveBeenCalledWith('/strains/1/', { rating: 10 })
      expect(store.items[0]!.rating).toBe(10)
      expect(store.items).toHaveLength(3)
    })

    it('drops the removed strain', async () => {
      routeGetByPath()
      const store = useStrainsStore()
      await store.fetchAll()

      mockApi.delete.mockResolvedValue({ data: null })
      await store.remove(1)
      expect(mockApi.delete).toHaveBeenCalledWith('/strains/1/')
      expect(store.items.map((s) => s.id)).toEqual([2, 3])
    })

    it('sets the error and rethrows when a create fails', async () => {
      const apiError = new ApiError({ message: 'bad', detail: 'unknown effect', status: 422 })
      mockApi.post.mockRejectedValue(apiError)
      const store = useStrainsStore()
      await expect(store.create({ name: 'Typo Kush' })).rejects.toThrow(ApiError)
      expect(store.error).toBe(apiError)
    })
  })
})
