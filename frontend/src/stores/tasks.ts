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

  const sortedTasks = computed(() =>
    [...tasks.value].sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority
      return new Date(a.add_date).getTime() - new Date(b.add_date).getTime()
    })
  )

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

  async function complete(id: number): Promise<CompletedTask> {
    error.value = null
    try {
      const response = await api.patch<CompletedTask>(`/tasks/${id}/complete/`)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      logger.info('task_completed', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_complete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function shift(id: number, positions: number) {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/shift/${positions}/`)
      const index = tasks.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      logger.info('task_shifted', { id, positions })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_shift_failed', { id, detail: apiError.detail, status: apiError.status })
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

  async function reorder() {
    error.value = null
    try {
      const response = await api.post<{ message: string }>('/tasks/reorder/')
      logger.info('tasks_reordered', { message: response.data.message })
      // Refetch so local state reflects the dense-ranked priorities
      await fetchTodo()
      return response.data.message
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('tasks_reorder_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function setPriority(id: number, priority: number) {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/`, { priority })
      const index = tasks.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      logger.info('task_priority_set', { id, priority })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_priority_set_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  return {
    tasks,
    completedTasks,
    loading,
    error,
    sortedTasks,
    totalCount,
    clearError,
    fetchTodo,
    fetchCompleted,
    search,
    create,
    complete,
    shift,
    remove,
    reorder,
    setPriority,
  }
})
