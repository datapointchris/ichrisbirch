import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { User } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  function setUser(newUser: User | null) {
    user.value = newUser
  }

  function clear() {
    user.value = null
  }

  return {
    user,
    loading,
    isAuthenticated,
    isAdmin,
    setUser,
    clear,
  }
})
