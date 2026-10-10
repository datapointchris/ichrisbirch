import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { User, UserPreferences } from '@/api/client'

const logger = createLogger('AuthStore')

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const preferences = computed(() => user.value?.preferences ?? null)

  function setUser(newUser: User | null) {
    user.value = newUser
  }

  function clear() {
    user.value = null
    error.value = null
  }

  function clearError() {
    error.value = null
  }

  async function fetchCurrentUser() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<User>('/users/me/')
      user.value = response.data
      logger.info('user_fetched', { id: response.data.id, email: response.data.email })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('user_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function updatePreferences(patch: Partial<UserPreferences>) {
    error.value = null
    try {
      const response = await api.patch<User>('/users/me/preferences/', patch)
      user.value = response.data
      logger.info('preferences_updated', { keys: Object.keys(patch) })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('preferences_update_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function reorderTasks(): Promise<{ message: string }> {
    error.value = null
    try {
      const response = await api.post<{ message: string }>('/tasks/reorder/')
      logger.info('tasks_reordered', { message: response.data.message })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('tasks_reorder_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    preferences,
    setUser,
    clear,
    clearError,
    fetchCurrentUser,
    updatePreferences,
    reorderTasks,
  }
})
