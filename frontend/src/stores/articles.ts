import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Article, ArticleCreate, ArticleUpdate, ArticleSummary } from '@/api/client'

const logger = createLogger('ArticlesStore')

export const useArticlesStore = defineStore('articles', () => {
  const articles = ref<Article[]>([])
  const currentArticle = ref<Article | null>(null)
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const summarizing = ref(false)

  const showArchived = ref(false)
  const searchQuery = ref('')
  const searchResults = ref<Article[]>([])
  const isSearchActive = computed(() => searchQuery.value.length > 0)

  const sortedArticles = computed(() => [...articles.value].sort((a, b) => b.save_date.localeCompare(a.save_date)))

  const displayedArticles = computed(() => (isSearchActive.value ? searchResults.value : sortedArticles.value))

  function clearError() {
    error.value = null
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Article[]>('/articles/', { params: { archived: showArchived.value } })
      articles.value = response.data
      logger.info('articles_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('articles_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrent() {
    error.value = null
    try {
      const response = await api.get<Article | null>('/articles/current/')
      currentArticle.value = response.data
      logger.info('current_article_fetched', { id: response.data?.id ?? null })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('current_article_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function create(input: ArticleCreate) {
    error.value = null
    try {
      const response = await api.post<Article>('/articles/', input)
      articles.value.push(response.data)
      logger.info('article_created', { id: response.data.id, title: response.data.title })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('article_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, input: ArticleUpdate) {
    error.value = null
    try {
      const response = await api.patch<Article>(`/articles/${id}/`, input)
      const index = articles.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        articles.value[index] = response.data
      }
      if (currentArticle.value?.id === id) {
        currentArticle.value = response.data
      }
      logger.info('article_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('article_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/articles/${id}/`)
      articles.value = articles.value.filter((a) => a.id !== id)
      if (currentArticle.value?.id === id) {
        currentArticle.value = null
      }
      logger.info('article_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('article_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function toggleFavorite(id: number) {
    const article = articles.value.find((a) => a.id === id)
    if (!article) return
    return update(id, { is_favorite: !article.is_favorite })
  }

  async function toggleArchive(id: number) {
    const article = articles.value.find((a) => a.id === id)
    if (!article) return
    const updated = await update(id, { is_archived: !article.is_archived })
    articles.value = articles.value.filter((a) => a.id !== id)
    return updated
  }

  async function setShowArchived(value: boolean) {
    showArchived.value = value
    await fetchAll()
  }

  async function makeCurrent(id: number) {
    const updated = await update(id, { is_current: true })
    currentArticle.value = updated
    return updated
  }

  async function removeCurrent(id: number) {
    const updated = await update(id, { is_current: false })
    if (currentArticle.value?.id === id) {
      currentArticle.value = null
    }
    return updated
  }

  async function markRead(id: number) {
    const article = articles.value.find((a) => a.id === id)
    if (!article) return
    const updated = await update(id, {
      is_archived: true,
      is_current: false,
      read_count: article.read_count + 1,
      last_read_date: new Date().toISOString(),
    })
    articles.value = articles.value.filter((a) => a.id !== id)
    if (currentArticle.value?.id === id) {
      currentArticle.value = null
    }
    return updated
  }

  async function summarizeUrl(url: string): Promise<ArticleSummary> {
    summarizing.value = true
    error.value = null
    try {
      const response = await api.post<ArticleSummary>('/articles/summarize/', { url })
      logger.info('article_summarized', { url })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('article_summarize_failed', { url, detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      summarizing.value = false
    }
  }

  async function search(query: string) {
    error.value = null
    try {
      const response = await api.get<Article[]>('/articles/search/', { params: { search: query } })
      searchQuery.value = query
      searchResults.value = response.data
      logger.info('articles_searched', { query, count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('articles_search_failed', { query, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function clearSearch() {
    searchQuery.value = ''
    searchResults.value = []
  }

  return {
    articles,
    currentArticle,
    loading,
    error,
    summarizing,
    showArchived,
    searchQuery,
    searchResults,
    isSearchActive,
    sortedArticles,
    displayedArticles,
    clearError,
    fetchAll,
    fetchCurrent,
    create,
    update,
    remove,
    toggleFavorite,
    toggleArchive,
    setShowArchived,
    makeCurrent,
    removeCurrent,
    markRead,
    summarizeUrl,
    search,
    clearSearch,
  }
})
