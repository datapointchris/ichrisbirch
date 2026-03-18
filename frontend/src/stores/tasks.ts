import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Task, TaskCreate, TaskCategory } from '@/api/client'

const logger = createLogger('TasksStore')

export const TASK_CATEGORIES: TaskCategory[] = [
  'Automotive',
  'Chore',
  'Computer',
  'Dingo',
  'Financial',
  'Home',
  'Kitchen',
  'Learn',
  'Personal',
  'Purchase',
  'Research',
  'Work',
]

export interface CompletedTask extends Task {
  complete_date: string
}

export function daysToComplete(task: CompletedTask): number {
  const add = new Date(task.add_date)
  const complete = new Date(task.complete_date)
  return Math.max(Math.round((complete.getTime() - add.getTime()) / (1000 * 60 * 60 * 24)), 1)
}

export function timeToComplete(task: CompletedTask): string {
  const days = daysToComplete(task)
  const weeks = Math.floor(days / 7)
  const remainder = days % 7
  return `${weeks} weeks, ${remainder} days`
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const completedTasks = ref<CompletedTask[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedTasks = computed(() => [...tasks.value].sort((a, b) => a.priority - b.priority))

  const overdueCount = computed(() => tasks.value.filter((t) => t.priority < 1).length)
  const criticalCount = computed(() => tasks.value.filter((t) => t.priority > 0 && t.priority <= 2).length)
  const dueSoonCount = computed(() => tasks.value.filter((t) => t.priority > 2 && t.priority <= 5).length)
  const totalCount = computed(() => tasks.value.length)

  function clearError() {
    error.value = null
  }

  async function fetchTodo() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Task[]>('/tasks/todo/')
      tasks.value = response.data
      logger.info('tasks_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('tasks_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchCompleted(startDate?: string, endDate?: string) {
    loading.value = true
    error.value = null
    try {
      const params: Record<string, string> = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const response = await api.get<CompletedTask[]>('/tasks/completed/', { params })
      completedTasks.value = response.data
      logger.info('completed_tasks_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('completed_tasks_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function search(query: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Task[]>('/tasks/search/', { params: { q: query } })
      const results = response.data
      tasks.value = results.filter((t) => !t.complete_date)
      completedTasks.value = results.filter((t) => t.complete_date) as CompletedTask[]
      logger.info('tasks_searched', { query, todo: tasks.value.length, completed: completedTasks.value.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('tasks_search_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function create(input: TaskCreate) {
    error.value = null
    try {
      const response = await api.post<Task>('/tasks/', input)
      tasks.value.push(response.data)
      logger.info('task_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function complete(id: number) {
    error.value = null
    try {
      await api.patch(`/tasks/${id}/complete/`)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      logger.info('task_completed', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_complete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function extend(id: number, days: number) {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/extend/${days}/`)
      const index = tasks.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      logger.info('task_extended', { id, days })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_extend_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/tasks/${id}/`)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      completedTasks.value = completedTasks.value.filter((t) => t.id !== id)
      logger.info('task_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function resetPriorities() {
    error.value = null
    try {
      const response = await api.post<{ message: string }>('/tasks/reset-priorities/')
      logger.info('priorities_reset', { message: response.data.message })
      return response.data.message
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('priorities_reset_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    tasks,
    completedTasks,
    loading,
    error,
    sortedTasks,
    overdueCount,
    criticalCount,
    dueSoonCount,
    totalCount,
    clearError,
    fetchTodo,
    fetchCompleted,
    search,
    create,
    complete,
    extend,
    remove,
    resetPriorities,
  }
})
