import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Book, BookCreate, BookUpdate, BookGoodreadsInfo } from '@/api/client'

const logger = createLogger('BooksStore')

export type BookStatus = 'sold' | 'abandoned' | 'read' | 'reading' | 'to-read'

export function deriveStatus(book: Book): BookStatus {
  // Use ownership status field for sold (not sell_date which seed data fills randomly)
  if (book.status === 'sold') return 'sold'
  if (book.abandoned) return 'abandoned'
  if (book.read_finish_date) return 'read'
  if (book.read_start_date) return 'reading'
  return 'to-read'
}

export const useBooksStore = defineStore('books', () => {
  const books = ref<Book[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const sortField = ref<string>('title')
  const sortDirection = ref<'asc' | 'desc'>('asc')
  const activeFilter = ref<string>('all')
  const searchQuery = ref('')
  const isSearchActive = ref(false)

  const statusCounts = computed(() => {
    const counts = { read: 0, reading: 0, toRead: 0, abandoned: 0, sold: 0, total: 0 }
    for (const book of books.value) {
      const status = deriveStatus(book)
      if (status === 'read') counts.read++
      else if (status === 'reading') counts.reading++
      else if (status === 'to-read') counts.toRead++
      else if (status === 'abandoned') counts.abandoned++
      else if (status === 'sold') counts.sold++
      counts.total++
    }
    return counts
  })

  const filteredBooks = computed(() => {
    if (activeFilter.value === 'all') return books.value
    return books.value.filter((book) => deriveStatus(book) === activeFilter.value)
  })

  const sortedBooks = computed(() => {
    const sorted = [...filteredBooks.value]
    const dir = sortDirection.value === 'asc' ? 1 : -1

    sorted.sort((a, b) => {
      switch (sortField.value) {
        case 'title':
          return dir * a.title.localeCompare(b.title)
        case 'author':
          return dir * a.author.localeCompare(b.author)
        case 'rating': {
          const ra = a.rating ?? 0
          const rb = b.rating ?? 0
          return dir * (ra - rb)
        }
        case 'finished': {
          const fa = a.read_finish_date ?? ''
          const fb = b.read_finish_date ?? ''
          return dir * fa.localeCompare(fb)
        }
        default:
          return 0
      }
    })
    return sorted
  })

  function clearError() {
    error.value = null
  }

  function setFilter(filter: string) {
    activeFilter.value = filter
  }

  function setSort(field: string) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'asc'
    }
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Book[]>('/books/')
      books.value = response.data
      logger.info('books_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('books_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: BookCreate) {
    error.value = null
    try {
      const response = await api.post<Book>('/books/', input)
      books.value.push(response.data)
      logger.info('book_created', { id: response.data.id, title: response.data.title })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('book_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: BookUpdate) {
    error.value = null
    try {
      const response = await api.patch<Book>(`/books/${id}/`, input)
      const index = books.value.findIndex((b) => b.id === id)
      if (index !== -1) {
        books.value[index] = response.data
      }
      logger.info('book_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('book_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/books/${id}/`)
      books.value = books.value.filter((b) => b.id !== id)
      logger.info('book_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('book_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function fetchGoodreadsInfo(isbn: string): Promise<BookGoodreadsInfo> {
    error.value = null
    try {
      const response = await api.post<BookGoodreadsInfo>('/books/goodreads/', { isbn })
      logger.info('goodreads_info_fetched', { isbn })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('goodreads_fetch_failed', { isbn, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function search(query: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Book[]>('/books/search/', { params: { q: query } })
      books.value = response.data
      searchQuery.value = query
      isSearchActive.value = true
      logger.info('books_search', { query, count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('books_search_failed', { query, detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function clearSearch() {
    searchQuery.value = ''
    isSearchActive.value = false
    await fetchAll()
  }

  return {
    books,
    loading,
    error,
    sortField,
    sortDirection,
    activeFilter,
    searchQuery,
    isSearchActive,
    statusCounts,
    filteredBooks,
    sortedBooks,
    clearError,
    setFilter,
    setSort,
    fetchAll,
    create,
    update,
    remove,
    fetchGoodreadsInfo,
    search,
    clearSearch,
  }
})
