import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Task, TaskCreate, TaskCategory, TaskUpdate } from '@/api/client'

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

export interface DroppedTask extends Task {
  drop_date: string
}

// The API's open-list order: pinned first, then rank_at, then add_date.
export function compareQueueOrder(a: Task, b: Task): number {
  if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
  const byRank = new Date(a.rank_at).getTime() - new Date(b.rank_at).getTime()
  if (byRank !== 0) return byRank
  return new Date(a.add_date).getTime() - new Date(b.add_date).getTime()
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const completedTasks = ref<CompletedTask[]>([])
  const droppedTasks = ref<DroppedTask[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const sortedTasks = computed(() => [...tasks.value].sort(compareQueueOrder))

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

  async function fetchDropped(startDate?: string, endDate?: string) {
    loading.value = true
    error.value = null
    try {
      const params: Record<string, string> = { status: 'dropped' }
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const response = await api.get<DroppedTask[]>('/tasks/', { params })
      droppedTasks.value = response.data
      logger.info('dropped_tasks_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('dropped_tasks_fetch_failed', { detail: apiError.detail, status: apiError.status })
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
      tasks.value = results.filter((t) => !t.complete_date && !t.drop_date)
      completedTasks.value = results.filter((t) => t.complete_date) as CompletedTask[]
      droppedTasks.value = results.filter((t) => t.drop_date) as DroppedTask[]
      logger.info('tasks_searched', {
        query,
        todo: tasks.value.length,
        completed: completedTasks.value.length,
        dropped: droppedTasks.value.length,
      })
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

  function replaceTask(task: Task) {
    const index = tasks.value.findIndex((t) => t.id === task.id)
    if (index !== -1) {
      tasks.value[index] = task
    }
  }

  async function snooze(id: number) {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/snooze/`)
      replaceTask(response.data)
      logger.info('task_snoozed', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_snooze_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function drop(id: number, reason?: string) {
    error.value = null
    try {
      await api.patch<Task>(`/tasks/${id}/drop/`, reason ? { reason } : undefined)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      logger.info('task_dropped', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_drop_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function reopen(id: number): Promise<Task> {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/reopen/`)
      droppedTasks.value = droppedTasks.value.filter((t) => t.id !== id)
      completedTasks.value = completedTasks.value.filter((t) => t.id !== id)
      tasks.value.push(response.data)
      logger.info('task_reopened', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_reopen_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function remove(id: number) {
    error.value = null
    try {
      await api.delete(`/tasks/${id}/`)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      completedTasks.value = completedTasks.value.filter((t) => t.id !== id)
      droppedTasks.value = droppedTasks.value.filter((t) => t.id !== id)
      logger.info('task_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function update(id: number, changes: TaskUpdate) {
    error.value = null
    try {
      const response = await api.patch<Task>(`/tasks/${id}/`, changes)
      replaceTask(response.data)
      logger.info('task_updated', { id, fields: Object.keys(changes) })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('task_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  function setPinned(id: number, pinned: boolean) {
    return update(id, { pinned })
  }

  function move(id: number, rankAt: string, pinned?: boolean) {
    return update(id, pinned === undefined ? { rank_at: rankAt } : { rank_at: rankAt, pinned })
  }

  return {
    tasks,
    completedTasks,
    droppedTasks,
    loading,
    error,
    sortedTasks,
    totalCount,
    clearError,
    fetchTodo,
    fetchCompleted,
    fetchDropped,
    search,
    create,
    complete,
    snooze,
    drop,
    reopen,
    remove,
    update,
    setPinned,
    move,
  }
})
