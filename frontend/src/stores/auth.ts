import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { User, UserPreferences, PersonalApiKey, PersonalApiKeyCreated } from '@/api/client'

const logger = createLogger('AuthStore')

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const apiKeys = ref<PersonalApiKey[]>([])
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
    apiKeys.value = []
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

  async function fetchApiKeys() {
    error.value = null
    try {
      const response = await api.get<PersonalApiKey[]>('/api-keys/')
      apiKeys.value = response.data
      logger.info('api_keys_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('api_keys_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function createApiKey(name: string): Promise<PersonalApiKeyCreated> {
    error.value = null
    try {
      const response = await api.post<PersonalApiKeyCreated>('/api-keys/', { name })
      // Add to local list without the full key (it's only shown once)
      apiKeys.value.unshift({
        id: response.data.id,
        name: response.data.name,
        key_prefix: response.data.key_prefix,
        created_at: response.data.created_at,
        last_used_at: response.data.last_used_at,
        revoked_at: response.data.revoked_at,
      })
      logger.info('api_key_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('api_key_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function revokeApiKey(id: number) {
    error.value = null
    try {
      await api.delete(`/api-keys/${id}/`)
      const key = apiKeys.value.find((k) => k.id === id)
      if (key) {
        key.revoked_at = new Date().toISOString()
      }
      logger.info('api_key_revoked', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('api_key_revoke_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function resetTaskPriorities(): Promise<{ message: string }> {
    error.value = null
    try {
      const response = await api.post<{ message: string }>('/tasks/reset-priorities/')
      logger.info('task_priorities_reset', { message: response.data.message })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_priorities_reset_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    user,
    apiKeys,
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
    fetchApiKeys,
    createApiKey,
    revokeApiKey,
    resetTaskPriorities,
  }
})
