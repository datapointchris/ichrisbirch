import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.user).toBeNull()
  })

  it('sets user and updates computed properties', () => {
    const store = useAuthStore()
    store.setUser({
      id: 1,
      alternative_id: 100,
      name: 'Test User',
      email: 'test@example.com',
      is_admin: true,
      created_on: '2026-01-01T00:00:00Z',
    })
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAdmin).toBe(true)
    expect(store.user?.name).toBe('Test User')
  })

  it('clears user state', () => {
    const store = useAuthStore()
    store.setUser({
      id: 1,
      alternative_id: 100,
      name: 'Test',
      email: 'test@example.com',
      is_admin: false,
      created_on: '2026-01-01T00:00:00Z',
    })
    store.clear()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })
})
