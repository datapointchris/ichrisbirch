import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useArticlesStore } from '../articles'
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

const testArticles = [
  {
    id: 1,
    title: 'Understanding TypeScript',
    url: 'https://example.com/typescript',
    tags: ['typescript', 'programming'],
    summary: 'A deep dive into TypeScript features.',
    notes: 'Very helpful article',
    save_date: '2026-01-15T10:00:00Z',
    last_read_date: '2026-02-01T10:00:00Z',
    read_count: 2,
    is_favorite: true,
    is_current: false,
    is_archived: false,
    review_days: 30,
  },
  {
    id: 2,
    title: 'Vue 3 Composition API',
    url: 'https://example.com/vue3',
    tags: ['vue', 'frontend'],
    summary: 'Guide to the Composition API.',
    save_date: '2026-02-10T10:00:00Z',
    read_count: 0,
    is_favorite: false,
    is_current: true,
    is_archived: false,
  },
  {
    id: 3,
    title: 'Docker Best Practices',
    url: 'https://example.com/docker',
    tags: ['docker', 'devops'],
    summary: 'Production-ready Docker patterns.',
    save_date: '2026-03-01T10:00:00Z',
    read_count: 1,
    is_favorite: false,
    is_current: false,
    is_archived: false,
  },
]

describe('useArticlesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useArticlesStore()
    expect(store.articles).toEqual([])
    expect(store.currentArticle).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.summarizing).toBe(false)
    expect(store.searchQuery).toBe('')
    expect(store.searchResults).toEqual([])
    expect(store.isSearchActive).toBe(false)
  })

  // --- fetchAll ---

  it('fetches articles from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testArticles })
    const store = useArticlesStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/articles/')
    expect(store.articles).toEqual(testArticles)
    expect(store.loading).toBe(false)
  })

  it('sets loading state during fetch', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.get.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useArticlesStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useArticlesStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useArticlesStore()
    store.error = new ApiError({ message: 'old', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- fetchCurrent ---

  it('fetches current article', async () => {
    const current = testArticles[1]
    mockApi.get.mockResolvedValue({ data: current })
    const store = useArticlesStore()

    await store.fetchCurrent()

    expect(mockApi.get).toHaveBeenCalledWith('/articles/current/')
    expect(store.currentArticle).toEqual(current)
  })

  it('sets currentArticle to null when no current', async () => {
    mockApi.get.mockResolvedValue({ data: null })
    const store = useArticlesStore()

    await store.fetchCurrent()

    expect(store.currentArticle).toBeNull()
  })

  // --- create ---

  it('creates an article and adds to state', async () => {
    const created = {
      id: 4,
      title: 'New Article',
      url: 'https://example.com/new',
      tags: [],
      summary: 'Summary',
      save_date: '2026-03-14T10:00:00Z',
      read_count: 0,
      is_favorite: false,
      is_current: false,
      is_archived: false,
    }
    mockApi.post.mockResolvedValue({ data: created })
    const store = useArticlesStore()

    const result = await store.create({
      title: 'New Article',
      url: 'https://example.com/new',
      summary: 'Summary',
      save_date: '2026-03-14T10:00:00Z',
    })

    expect(mockApi.post).toHaveBeenCalledWith('/articles/', {
      title: 'New Article',
      url: 'https://example.com/new',
      summary: 'Summary',
      save_date: '2026-03-14T10:00:00Z',
    })
    expect(result).toEqual(created)
    expect(store.articles).toHaveLength(1)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useArticlesStore()

    await expect(store.create({ title: 'X', url: 'x', summary: 'x', save_date: 'x' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- update ---

  it('updates an article in place', async () => {
    const updated = { ...testArticles[0]!, title: 'Updated Title' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await store.update(1, { title: 'Updated Title' })

    expect(mockApi.patch).toHaveBeenCalledWith('/articles/1/', { title: 'Updated Title' })
    expect(store.articles.find((a) => a.id === 1)!.title).toBe('Updated Title')
  })

  it('updates currentArticle when it matches updated id', async () => {
    const updated = { ...testArticles[1]!, title: 'Updated Current' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]
    store.currentArticle = { ...testArticles[1]! }

    await store.update(2, { title: 'Updated Current' })

    expect(store.currentArticle!.title).toBe('Updated Current')
  })

  // --- remove ---

  it('removes an article from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/articles/2/')
    expect(store.articles).toHaveLength(2)
    expect(store.articles.find((a) => a.id === 2)).toBeUndefined()
  })

  it('clears currentArticle when removing current article', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useArticlesStore()
    store.articles = [...testArticles]
    store.currentArticle = { ...testArticles[1]! }

    await store.remove(2)

    expect(store.currentArticle).toBeNull()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.articles).toHaveLength(3)
  })

  // --- toggleFavorite ---

  it('toggles favorite status', async () => {
    const updated = { ...testArticles[0]!, is_favorite: false }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await store.toggleFavorite(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/articles/1/', { is_favorite: false })
    expect(store.articles.find((a) => a.id === 1)!.is_favorite).toBe(false)
  })

  // --- toggleArchive ---

  it('archives an article and removes from list', async () => {
    const updated = { ...testArticles[2]!, is_archived: true }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await store.toggleArchive(3)

    expect(mockApi.patch).toHaveBeenCalledWith('/articles/3/', { is_archived: true })
    expect(store.articles.find((a) => a.id === 3)).toBeUndefined()
  })

  // --- makeCurrent ---

  it('sets an article as current', async () => {
    const updated = { ...testArticles[2]!, is_current: true }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]

    await store.makeCurrent(3)

    expect(mockApi.patch).toHaveBeenCalledWith('/articles/3/', { is_current: true })
    expect(store.currentArticle!.id).toBe(3)
  })

  // --- removeCurrent ---

  it('removes current status from an article', async () => {
    const updated = { ...testArticles[1]!, is_current: false }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]
    store.currentArticle = { ...testArticles[1]! }

    await store.removeCurrent(2)

    expect(mockApi.patch).toHaveBeenCalledWith('/articles/2/', { is_current: false })
    expect(store.currentArticle).toBeNull()
  })

  // --- markRead ---

  it('marks an article as read, archives it, removes from list', async () => {
    const updated = { ...testArticles[1]!, is_archived: true, is_current: false, read_count: 1 }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useArticlesStore()
    store.articles = [...testArticles]
    store.currentArticle = { ...testArticles[1]! }

    await store.markRead(2)

    expect(mockApi.patch).toHaveBeenCalledWith(
      '/articles/2/',
      expect.objectContaining({
        is_archived: true,
        is_current: false,
        read_count: 1,
      })
    )
    expect(store.articles.find((a) => a.id === 2)).toBeUndefined()
    expect(store.currentArticle).toBeNull()
  })

  // --- summarizeUrl ---

  it('summarizes a URL and returns result', async () => {
    const summary = { title: 'Article Title', summary: 'A great summary', tags: ['tag1', 'tag2'] }
    mockApi.post.mockResolvedValue({ data: summary })
    const store = useArticlesStore()

    const result = await store.summarizeUrl('https://example.com/article')

    expect(mockApi.post).toHaveBeenCalledWith('/articles/summarize/', { url: 'https://example.com/article' })
    expect(result).toEqual(summary)
    expect(store.summarizing).toBe(false)
  })

  it('sets summarizing state during summarize', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.post.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useArticlesStore()

    const promise = store.summarizeUrl('https://example.com')
    expect(store.summarizing).toBe(true)

    resolvePromise({ data: { title: '', summary: '', tags: [] } })
    await promise
    expect(store.summarizing).toBe(false)
  })

  it('sets error on summarize failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'OpenAI error', status: 500 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useArticlesStore()

    await expect(store.summarizeUrl('https://example.com')).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.summarizing).toBe(false)
  })

  // --- search ---

  it('searches articles by tags', async () => {
    const results = [testArticles[0]!]
    mockApi.get.mockResolvedValue({ data: results })
    const store = useArticlesStore()

    await store.search('typescript')

    expect(mockApi.get).toHaveBeenCalledWith('/articles/search/', { params: { search: 'typescript' } })
    expect(store.searchQuery).toBe('typescript')
    expect(store.searchResults).toEqual(results)
    expect(store.isSearchActive).toBe(true)
  })

  it('clears search state', async () => {
    const store = useArticlesStore()
    store.searchQuery = 'test'
    store.searchResults = [...testArticles]

    await store.clearSearch()

    expect(store.searchQuery).toBe('')
    expect(store.searchResults).toEqual([])
    expect(store.isSearchActive).toBe(false)
  })

  // --- sortedArticles ---

  it('sorts articles by save_date descending', () => {
    const store = useArticlesStore()
    store.articles = [...testArticles]
    const sorted = store.sortedArticles
    expect(sorted[0]!.title).toBe('Docker Best Practices') // 2026-03-01
    expect(sorted[1]!.title).toBe('Vue 3 Composition API') // 2026-02-10
    expect(sorted[2]!.title).toBe('Understanding TypeScript') // 2026-01-15
  })

  // --- displayedArticles ---

  it('returns sorted articles when search is not active', () => {
    const store = useArticlesStore()
    store.articles = [...testArticles]
    expect(store.displayedArticles).toEqual(store.sortedArticles)
  })

  it('returns search results when search is active', () => {
    const store = useArticlesStore()
    store.articles = [...testArticles]
    store.searchQuery = 'typescript'
    store.searchResults = [testArticles[0]!]
    expect(store.displayedArticles).toEqual([testArticles[0]!])
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useArticlesStore()
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
    const store = useArticlesStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
