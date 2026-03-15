import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type {
  SchedulerJob,
  SchedulerJobRun,
  SystemHealth,
  RecentError,
  User,
  EnvironmentConfigSection,
  SmokeTestReport,
} from '@/api/client'

const logger = createLogger('AdminStore')

export const useAdminStore = defineStore('admin', () => {
  const error = ref<ApiError | null>(null)

  // System health
  const systemHealth = ref<SystemHealth | null>(null)
  const systemHealthLoading = ref(false)

  // Recent errors
  const recentErrors = ref<RecentError[]>([])
  const recentErrorsLoading = ref(false)

  // Scheduler
  const schedulerJobs = ref<SchedulerJob[]>([])
  const schedulerJobsLoading = ref(false)
  const jobHistory = ref<SchedulerJobRun[]>([])
  const jobHistoryLoading = ref(false)

  // Users
  const users = ref<User[]>([])
  const usersLoading = ref(false)

  // Smoke tests
  const smokeReport = ref<SmokeTestReport | null>(null)
  const smokeTestsRunning = ref(false)

  // Config
  const config = ref<EnvironmentConfigSection[]>([])
  const configLoading = ref(false)

  // --- System health ---

  async function fetchSystemHealth() {
    systemHealthLoading.value = true
    error.value = null
    try {
      const response = await api.get('/admin/system/health/')
      systemHealth.value = response.data
      logger.info('system_health_fetched')
    } catch (e) {
      error.value =
        e instanceof ApiError
          ? e
          : new ApiError({ message: 'Failed to fetch system health', detail: 'Failed to fetch system health', status: 500 })
      logger.error('system_health_fetch_failed', { error: error.value.detail })
    } finally {
      systemHealthLoading.value = false
    }
  }

  async function fetchRecentErrors() {
    recentErrorsLoading.value = true
    try {
      const response = await api.get('/admin/system/errors/')
      recentErrors.value = response.data
      logger.info('recent_errors_fetched', { count: recentErrors.value.length })
    } catch (e) {
      logger.error('recent_errors_fetch_failed', { error: e instanceof ApiError ? e.detail : String(e) })
    } finally {
      recentErrorsLoading.value = false
    }
  }

  // --- Scheduler ---

  async function fetchSchedulerJobs() {
    schedulerJobsLoading.value = true
    error.value = null
    try {
      const response = await api.get('/admin/scheduler/jobs/')
      schedulerJobs.value = response.data
      logger.info('scheduler_jobs_fetched', { count: schedulerJobs.value.length })
    } catch (e) {
      error.value =
        e instanceof ApiError
          ? e
          : new ApiError({ message: 'Failed to fetch scheduler jobs', detail: 'Failed to fetch scheduler jobs', status: 500 })
      logger.error('scheduler_jobs_fetch_failed', { error: error.value.detail })
    } finally {
      schedulerJobsLoading.value = false
    }
  }

  async function pauseJob(jobId: string) {
    try {
      const response = await api.post(`/admin/scheduler/jobs/${jobId}/pause/`)
      const idx = schedulerJobs.value.findIndex((j) => j.id === jobId)
      if (idx !== -1) schedulerJobs.value[idx] = response.data
      logger.info('scheduler_job_paused', { job_id: jobId })
    } catch (e) {
      error.value = e instanceof ApiError ? e : new ApiError({ message: 'Failed to pause job', detail: 'Failed to pause job', status: 500 })
      logger.error('scheduler_job_pause_failed', { job_id: jobId, error: error.value.detail })
      throw e
    }
  }

  async function resumeJob(jobId: string) {
    try {
      const response = await api.post(`/admin/scheduler/jobs/${jobId}/resume/`)
      const idx = schedulerJobs.value.findIndex((j) => j.id === jobId)
      if (idx !== -1) schedulerJobs.value[idx] = response.data
      logger.info('scheduler_job_resumed', { job_id: jobId })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to resume job', detail: 'Failed to resume job', status: 500 })
      logger.error('scheduler_job_resume_failed', { job_id: jobId, error: error.value.detail })
      throw e
    }
  }

  async function deleteJob(jobId: string) {
    try {
      await api.delete(`/admin/scheduler/jobs/${jobId}/`)
      schedulerJobs.value = schedulerJobs.value.filter((j) => j.id !== jobId)
      logger.info('scheduler_job_deleted', { job_id: jobId })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to delete job', detail: 'Failed to delete job', status: 500 })
      logger.error('scheduler_job_delete_failed', { job_id: jobId, error: error.value.detail })
      throw e
    }
  }

  async function fetchJobHistory(jobId?: string) {
    jobHistoryLoading.value = true
    try {
      const params = jobId ? { job_id: jobId } : {}
      const response = await api.get('/admin/scheduler/history/', { params })
      jobHistory.value = response.data
      logger.info('job_history_fetched', { count: jobHistory.value.length, job_id: jobId })
    } catch (e) {
      logger.error('job_history_fetch_failed', { error: e instanceof ApiError ? e.detail : String(e) })
    } finally {
      jobHistoryLoading.value = false
    }
  }

  // --- Users ---

  async function fetchUsers() {
    usersLoading.value = true
    error.value = null
    try {
      const response = await api.get('/users/')
      users.value = response.data
      logger.info('users_fetched', { count: users.value.length })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to fetch users', detail: 'Failed to fetch users', status: 500 })
      logger.error('users_fetch_failed', { error: error.value.detail })
    } finally {
      usersLoading.value = false
    }
  }

  async function updateUserAdmin(userId: number, isAdmin: boolean) {
    try {
      await api.patch(`/users/${userId}/`, { is_admin: isAdmin })
      const user = users.value.find((u) => u.id === userId)
      if (user) user.is_admin = isAdmin
      logger.info('user_admin_updated', { user_id: userId, is_admin: isAdmin })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to update user', detail: 'Failed to update user', status: 500 })
      logger.error('user_admin_update_failed', { user_id: userId, error: error.value.detail })
      throw e
    }
  }

  // --- Config ---

  async function fetchConfig() {
    configLoading.value = true
    error.value = null
    try {
      const response = await api.get('/admin/config/')
      config.value = response.data
      logger.info('config_fetched', { sections: config.value.length })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to fetch config', detail: 'Failed to fetch config', status: 500 })
      logger.error('config_fetch_failed', { error: error.value.detail })
    } finally {
      configLoading.value = false
    }
  }

  // --- Smoke tests ---

  async function runSmokeTests() {
    smokeTestsRunning.value = true
    error.value = null
    try {
      const response = await api.post('/admin/smoke-tests/')
      smokeReport.value = response.data
      logger.info('smoke_tests_completed', {
        total: smokeReport.value!.total,
        passed: smokeReport.value!.passed,
        failed: smokeReport.value!.failed,
      })
    } catch (e) {
      error.value =
        e instanceof ApiError ? e : new ApiError({ message: 'Failed to run smoke tests', detail: 'Failed to run smoke tests', status: 500 })
      logger.error('smoke_tests_failed', { error: error.value.detail })
    } finally {
      smokeTestsRunning.value = false
    }
  }

  return {
    error,
    systemHealth,
    systemHealthLoading,
    recentErrors,
    recentErrorsLoading,
    schedulerJobs,
    schedulerJobsLoading,
    jobHistory,
    jobHistoryLoading,
    users,
    usersLoading,
    config,
    configLoading,
    fetchSystemHealth,
    fetchRecentErrors,
    fetchSchedulerJobs,
    pauseJob,
    resumeJob,
    deleteJob,
    fetchJobHistory,
    fetchUsers,
    updateUserAdmin,
    fetchConfig,
    smokeReport,
    smokeTestsRunning,
    runSmokeTests,
  }
})
