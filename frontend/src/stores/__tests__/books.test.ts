import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBooksStore } from '../books'
import { ApiError } from '@/api/errors'
import type { Book } from '@/api/client'

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

// Test data covering all 4 progress values
const testBooks: Book[] = [
  {
    id: 1,
    title: 'Clean Code',
    author: 'Robert Martin',
    tags: ['programming', 'software'],
    ownership: 'owned',
    progress: 'read',
    read_start_date: '2025-01-01T00:00:00',
    read_finish_date: '2025-02-15T00:00:00',
    rating: 5,
  },
  {
    id: 2,
    title: 'Dune',
    author: 'Frank Herbert',
    tags: ['sci-fi', 'fiction'],
    ownership: 'owned',
    progress: 'reading',
    read_start_date: '2025-06-01T00:00:00',
  },
  {
    id: 3,
    title: 'The Pragmatic Programmer',
    author: 'David Thomas',
    tags: ['programming'],
    ownership: 'owned',
    progress: 'unread',
  },
  {
    id: 4,
    title: 'Old Man and the Sea',
    author: 'Ernest Hemingway',
    tags: ['fiction', 'classic'],
    ownership: 'owned',
    progress: 'abandoned',
  },
  {
    id: 5,
    title: 'JavaScript: The Good Parts',
    author: 'Douglas Crockford',
    tags: ['programming', 'javascript'],
    ownership: 'sold',
    progress: 'read',
    sell_date: '2025-03-01T00:00:00',
    sell_price: 12.0,
    read_finish_date: '2024-12-01T00:00:00',
    rating: 3,
  },
]

describe('useBooksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useBooksStore()
    expect(store.books).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.sortField).toBe('title')
    expect(store.sortDirection).toBe('asc')
    expect(store.activeFilter).toBe('all')
    expect(store.searchQuery).toBe('')
    expect(store.isSearchActive).toBe(false)
  })

  // --- fetchAll ---

  it('fetches books from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testBooks })
    const store = useBooksStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/books/')
    expect(store.books).toEqual(testBooks)
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
    const store = useBooksStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useBooksStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useBooksStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates a book and adds it to the list', async () => {
    const newBook = { id: 6, title: 'New Book', author: 'Test Author', tags: ['test'] }
    mockApi.post.mockResolvedValue({ data: newBook })
    const store = useBooksStore()

    const result = await store.create({ title: 'New Book', author: 'Test Author', tags: ['test'] })

    expect(mockApi.post).toHaveBeenCalledWith('/books/', { title: 'New Book', author: 'Test Author', tags: ['test'] })
    expect(result).toEqual(newBook)
    expect(store.books).toContainEqual(newBook)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({
      message: 'API 422',
      detail: 'Validation error',
      status: 422,
      validationErrors: [{ field: 'tags', message: 'at least one tag is required' }],
    })
    mockApi.post.mockRejectedValue(apiError)
    const store = useBooksStore()

    await expect(store.create({ title: 'Bad', author: 'Bad', tags: [] })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.books).toEqual([])
  })

  // --- update ---

  it('updates a book in place', async () => {
    const updated = { ...testBooks[0], title: 'Clean Code 2nd Ed' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useBooksStore()
    store.books = [...testBooks]

    const result = await store.update(1, { title: 'Clean Code 2nd Ed' })

    expect(mockApi.patch).toHaveBeenCalledWith('/books/1/', { title: 'Clean Code 2nd Ed' })
    expect(result).toEqual(updated)
    expect(store.books.find((b) => b.id === 1)!.title).toBe('Clean Code 2nd Ed')
  })

  it('sets error state on update failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Book not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useBooksStore()

    await expect(store.update(999, { title: 'Ghost' })).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(404)
  })

  // --- remove ---

  it('removes a book from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useBooksStore()
    store.books = [...testBooks]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/books/2/')
    expect(store.books).toHaveLength(4)
    expect(store.books.find((b) => b.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useBooksStore()
    store.books = [...testBooks]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.books).toHaveLength(5)
    expect(store.error!.status).toBe(500)
  })

  // --- fetchGoodreadsInfo ---

  it('returns goodreads info without modifying store', async () => {
    const goodreadsInfo = {
      title: 'Clean Code',
      author: 'Robert C. Martin',
      tags: 'Programming, Software',
      goodreads_url: 'https://goodreads.com/book/1',
    }
    mockApi.post.mockResolvedValue({ data: goodreadsInfo })
    const store = useBooksStore()

    const result = await store.fetchGoodreadsInfo('978-0132350884')

    expect(mockApi.post).toHaveBeenCalledWith('/books/goodreads/', { isbn: '978-0132350884' })
    expect(result).toEqual(goodreadsInfo)
    expect(store.books).toEqual([])
  })

  it('sets error on goodreads failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Goodreads unreachable', status: 500 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useBooksStore()

    await expect(store.fetchGoodreadsInfo('bad-isbn')).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(500)
  })

  // --- statusCounts ---

  it('computes status counts for all progress values', () => {
    const store = useBooksStore()
    store.books = [...testBooks]

    expect(store.statusCounts).toEqual({
      read: 2,
      reading: 1,
      unread: 1,
      abandoned: 1,
      total: 5,
    })
  })

  // --- filteredBooks ---

  it('returns all books when filter is all', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.activeFilter = 'all'

    expect(store.filteredBooks).toHaveLength(5)
  })

  it('filters by read progress', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.setFilter('read')

    expect(store.filteredBooks).toHaveLength(2)
  })

  it('filters by reading progress', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.setFilter('reading')

    expect(store.filteredBooks).toHaveLength(1)
    expect(store.filteredBooks[0].title).toBe('Dune')
  })

  it('filters by unread progress', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.setFilter('unread')

    expect(store.filteredBooks).toHaveLength(1)
    expect(store.filteredBooks[0].title).toBe('The Pragmatic Programmer')
  })

  it('filters by abandoned progress', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.setFilter('abandoned')

    expect(store.filteredBooks).toHaveLength(1)
    expect(store.filteredBooks[0].title).toBe('Old Man and the Sea')
  })

  // --- sortedBooks ---

  it('sorts by title ascending', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.sortField = 'title'
    store.sortDirection = 'asc'

    const titles = store.sortedBooks.map((b) => b.title)
    expect(titles).toEqual(['Clean Code', 'Dune', 'JavaScript: The Good Parts', 'Old Man and the Sea', 'The Pragmatic Programmer'])
  })

  it('sorts by author descending', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.sortField = 'author'
    store.sortDirection = 'desc'

    const first = store.sortedBooks[0]
    expect(first.author).toBe('Robert Martin')
  })

  it('sorts by rating ascending (nulls as 0)', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.sortField = 'rating'
    store.sortDirection = 'asc'

    const ratings = store.sortedBooks.map((b) => b.rating ?? 0)
    expect(ratings[0]).toBe(0)
    expect(ratings[ratings.length - 1]).toBe(5)
  })

  it('sorts by finished date ascending', () => {
    const store = useBooksStore()
    store.books = [...testBooks]
    store.sortField = 'finished'
    store.sortDirection = 'asc'

    // Books without finish date sort first (empty string < any date)
    const first = store.sortedBooks[0]
    expect(first.read_finish_date).toBeUndefined()
  })

  // --- setSort ---

  it('toggles direction when same field clicked', () => {
    const store = useBooksStore()
    expect(store.sortField).toBe('title')
    expect(store.sortDirection).toBe('asc')

    store.setSort('title')
    expect(store.sortDirection).toBe('desc')

    store.setSort('title')
    expect(store.sortDirection).toBe('asc')
  })

  it('resets to asc when new field selected', () => {
    const store = useBooksStore()
    store.sortDirection = 'desc'

    store.setSort('author')
    expect(store.sortField).toBe('author')
    expect(store.sortDirection).toBe('asc')
  })

  // --- search ---

  it('searches books and sets search state', async () => {
    const searchResults = [testBooks[0]]
    mockApi.get.mockResolvedValue({ data: searchResults })
    const store = useBooksStore()

    await store.search('clean code')

    expect(mockApi.get).toHaveBeenCalledWith('/books/search/', { params: { q: 'clean code' } })
    expect(store.books).toEqual(searchResults)
    expect(store.searchQuery).toBe('clean code')
    expect(store.isSearchActive).toBe(true)
    expect(store.loading).toBe(false)
  })

  it('sets error on search failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Search failed', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useBooksStore()

    await expect(store.search('bad query')).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  // --- clearSearch ---

  it('clears search state and re-fetches all books', async () => {
    mockApi.get.mockResolvedValue({ data: testBooks })
    const store = useBooksStore()
    store.searchQuery = 'old query'
    store.isSearchActive = true

    await store.clearSearch()

    expect(store.searchQuery).toBe('')
    expect(store.isSearchActive).toBe(false)
    expect(mockApi.get).toHaveBeenCalledWith('/books/')
    expect(store.books).toEqual(testBooks)
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useBooksStore()
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
    const store = useBooksStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
