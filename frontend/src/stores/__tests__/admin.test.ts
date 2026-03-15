import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAdminStore } from '../admin'
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

const testSystemHealth = {
  server: { environment: 'testing', api_url: 'http://api:8000', server_time: '2026-03-15T12:00:00' },
  docker: [
    { name: 'icb-dev-api', status: 'running', started_at: '2026-03-15T10:00:00Z', image: 'ichrisbirch:dev' },
    { name: 'icb-dev-postgres', status: 'running', started_at: '2026-03-15T10:00:00Z', image: 'postgres:16' },
  ],
  database: {
    tables: [{ schema_name: 'public', table_name: 'tasks', row_count: 42 }],
    total_size_mb: 15.5,
    active_connections: 3,
  },
  redis: { key_count: 5, memory_used_human: '1.2M', connected_clients: 2, uptime_seconds: 86400 },
  disk: { total_gb: 100, used_gb: 45, free_gb: 55, percent_used: 45.0 },
}

const testSchedulerJobs = [
  {
    id: 'decrease_task_priority_daily',
    name: 'decrease_task_priority',
    trigger: 'cron[day="*", hour="1"]',
    next_run_time: '2026-03-16T01:00:00',
    time_until_next_run: '6 hours',
    is_paused: false,
  },
  {
    id: 'make_logs',
    name: 'make_logs',
    trigger: 'cron[second="15"]',
    next_run_time: null,
    time_until_next_run: 'Paused',
    is_paused: true,
  },
]

describe('useAdminStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetchSystemHealth', () => {
    it('fetches and stores system health data', async () => {
      mockApi.get.mockResolvedValueOnce({ data: testSystemHealth })
      const store = useAdminStore()
      await store.fetchSystemHealth()
      expect(store.systemHealth).toEqual(testSystemHealth)
      expect(store.systemHealthLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      const apiError = new ApiError({ message: 'Server error', detail: 'Internal error', status: 500 })
      mockApi.get.mockRejectedValueOnce(apiError)
      const store = useAdminStore()
      await store.fetchSystemHealth()
      expect(store.error).toBe(apiError)
      expect(store.systemHealthLoading).toBe(false)
    })
  })

  describe('fetchSchedulerJobs', () => {
    it('fetches and stores scheduler jobs', async () => {
      mockApi.get.mockResolvedValueOnce({ data: testSchedulerJobs })
      const store = useAdminStore()
      await store.fetchSchedulerJobs()
      expect(store.schedulerJobs).toEqual(testSchedulerJobs)
      expect(store.schedulerJobs).toHaveLength(2)
    })
  })

  describe('pauseJob', () => {
    it('updates job in list after pausing', async () => {
      const store = useAdminStore()
      store.schedulerJobs = [...testSchedulerJobs]

      const pausedJob = { ...testSchedulerJobs[0], is_paused: true, next_run_time: null, time_until_next_run: 'Paused' }
      mockApi.post.mockResolvedValueOnce({ data: pausedJob })

      await store.pauseJob('decrease_task_priority_daily')
      expect(store.schedulerJobs[0].is_paused).toBe(true)
    })
  })

  describe('resumeJob', () => {
    it('updates job in list after resuming', async () => {
      const store = useAdminStore()
      store.schedulerJobs = [...testSchedulerJobs]

      const resumedJob = {
        ...testSchedulerJobs[1],
        is_paused: false,
        next_run_time: '2026-03-15T12:00:15',
        time_until_next_run: '15 seconds',
      }
      mockApi.post.mockResolvedValueOnce({ data: resumedJob })

      await store.resumeJob('make_logs')
      expect(store.schedulerJobs[1].is_paused).toBe(false)
    })
  })

  describe('deleteJob', () => {
    it('removes job from list', async () => {
      const store = useAdminStore()
      store.schedulerJobs = [...testSchedulerJobs]
      mockApi.delete.mockResolvedValueOnce({})

      await store.deleteJob('make_logs')
      expect(store.schedulerJobs).toHaveLength(1)
      expect(store.schedulerJobs[0].id).toBe('decrease_task_priority_daily')
    })
  })

  describe('fetchUsers', () => {
    it('fetches and stores users', async () => {
      const users = [
        {
          id: 1,
          alternative_id: 123,
          name: 'Admin',
          email: 'admin@test.com',
          is_admin: true,
          created_on: '2026-01-01',
          last_login: null,
          preferences: {},
        },
      ]
      mockApi.get.mockResolvedValueOnce({ data: users })
      const store = useAdminStore()
      await store.fetchUsers()
      expect(store.users).toEqual(users)
    })
  })

  describe('updateUserAdmin', () => {
    it('updates admin status in local state', async () => {
      const store = useAdminStore()
      store.users = [
        {
          id: 1,
          alternative_id: 123,
          name: 'User',
          email: 'user@test.com',
          is_admin: false,
          created_on: '2026-01-01',
          last_login: null,
          preferences: {},
        },
      ]
      mockApi.patch.mockResolvedValueOnce({ data: {} })

      await store.updateUserAdmin(1, true)
      expect(store.users[0].is_admin).toBe(true)
    })
  })

  describe('fetchConfig', () => {
    it('fetches and stores config sections', async () => {
      const sections = [
        { name: '_general', settings: { ENVIRONMENT: 'testing' } },
        { name: 'auth', settings: { jwt_secret_key: '***MASKED***' } },
      ]
      mockApi.get.mockResolvedValueOnce({ data: sections })
      const store = useAdminStore()
      await store.fetchConfig()
      expect(store.config).toEqual(sections)
      expect(store.config).toHaveLength(2)
    })
  })
})
