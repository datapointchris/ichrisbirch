import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type {
  ProjectWithItemCount,
  ProjectCreate,
  ProjectUpdate,
  ProjectItem,
  ProjectItemCreate,
  ProjectItemUpdate,
  ProjectItemDetail,
  ProjectItemInProject,
  ProjectItemReorder,
  ProjectItemMembershipCreate,
  ProjectItemDependencyCreate,
} from '@/api/client'

const logger = createLogger('ProjectsStore')

export const useProjectsStore = defineStore('projects', () => {
  // --- Project state ---
  const projects = ref<ProjectWithItemCount[]>([])
  const selectedProjectId = ref<number | null>(null)
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  // --- Item state (scoped to selected project) ---
  const items = ref<ProjectItemInProject[]>([])
  const itemsLoading = ref(false)
  const itemBlockers = ref<Record<number, ProjectItem[]>>({})

  const sortedProjects = computed(() => [...projects.value].sort((a, b) => a.position - b.position))

  const sortedItems = computed(() => [...items.value].sort((a, b) => a.position - b.position))

  const selectedProject = computed(() => projects.value.find((p) => p.id === selectedProjectId.value) ?? null)

  function clearError() {
    error.value = null
  }

  // --- Project CRUD ---

  async function fetchProjects() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<ProjectWithItemCount[]>('/projects/')
      projects.value = response.data
      logger.info('projects_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('projects_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function createProject(input: ProjectCreate) {
    error.value = null
    try {
      await api.post('/projects/', input)
      await fetchProjects()
      logger.info('project_created', { name: input.name })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('project_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function updateProject(id: number, input: ProjectUpdate) {
    error.value = null
    try {
      await api.patch(`/projects/${id}/`, input)
      await fetchProjects()
      logger.info('project_updated', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('project_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function removeProject(id: number) {
    error.value = null
    try {
      await api.delete(`/projects/${id}/`)
      projects.value = projects.value.filter((p) => p.id !== id)
      if (selectedProjectId.value === id) {
        selectedProjectId.value = null
        items.value = []
      }
      logger.info('project_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('project_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  // --- Item operations (scoped to selected project) ---

  async function fetchItems(projectId: number) {
    selectedProjectId.value = projectId
    itemsLoading.value = true
    itemBlockers.value = {}
    error.value = null
    try {
      const response = await api.get<ProjectItemInProject[]>(`/projects/${projectId}/items/`)
      items.value = response.data
      logger.info('items_fetched', { project_id: projectId, count: response.data.length })
      fetchItemBlockers()
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('items_fetch_failed', {
        project_id: projectId,
        detail: apiError.detail,
        status: apiError.status,
      })
      throw apiError
    } finally {
      itemsLoading.value = false
    }
  }

  async function createItem(input: ProjectItemCreate) {
    error.value = null
    try {
      const response = await api.post<ProjectItemDetail>('/project-items/', input)
      logger.info('item_created', { id: response.data.id, title: input.title })
      // Refresh both projects (item counts) and items list
      await fetchProjects()
      if (selectedProjectId.value !== null) {
        await fetchItems(selectedProjectId.value)
      }
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function updateItem(id: number, input: ProjectItemUpdate) {
    error.value = null
    try {
      const response = await api.patch<ProjectItem>(`/project-items/${id}/`, input)
      const index = items.value.findIndex((i) => i.id === id)
      const existing = items.value[index]
      if (index !== -1 && existing) {
        items.value[index] = { ...response.data, position: existing.position }
      }
      logger.info('item_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function removeItem(id: number) {
    error.value = null
    try {
      await api.delete(`/project-items/${id}/`)
      items.value = items.value.filter((i) => i.id !== id)
      await fetchProjects()
      logger.info('item_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function reorderItem(id: number, input: ProjectItemReorder) {
    error.value = null
    try {
      await api.patch(`/project-items/${id}/reorder/`, input)
      logger.info('item_reordered', { id, project_id: input.project_id, position: input.position })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_reorder_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function reorderItems(orderedIds: number[]) {
    if (selectedProjectId.value === null) return
    const projectId = selectedProjectId.value
    error.value = null

    try {
      const updates: Promise<unknown>[] = []

      for (const [index, id] of orderedIds.entries()) {
        const item = items.value.find((i) => i.id === id)
        if (item && item.position !== index) {
          updates.push(api.patch(`/project-items/${id}/reorder/`, { project_id: projectId, position: index }))
        }
      }

      if (updates.length > 0) {
        await Promise.all(updates)
        for (const [index, id] of orderedIds.entries()) {
          const item = items.value.find((i) => i.id === id)
          if (item) item.position = index
        }
        logger.info('items_reordered', { project_id: projectId, count: updates.length })
      }
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('items_reorder_failed', { detail: apiError.detail })
      await fetchItems(projectId)
      throw apiError
    }
  }

  async function reorderProjects(orderedIds: number[]) {
    error.value = null

    try {
      const updates: Promise<unknown>[] = []

      for (const [index, id] of orderedIds.entries()) {
        const project = projects.value.find((p) => p.id === id)
        if (project && project.position !== index) {
          updates.push(api.patch(`/projects/${id}/`, { position: index }))
        }
      }

      if (updates.length > 0) {
        await Promise.all(updates)
        for (const [index, id] of orderedIds.entries()) {
          const project = projects.value.find((p) => p.id === id)
          if (project) project.position = index
        }
        logger.info('projects_reordered', { count: updates.length })
      }
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('projects_reorder_failed', { detail: apiError.detail })
      await fetchProjects()
      throw apiError
    }
  }

  async function completeItem(id: number) {
    return updateItem(id, { completed: true })
  }

  async function archiveItem(id: number) {
    return updateItem(id, { archived: true })
  }

  // --- Blocker tracking ---

  async function fetchItemBlockers() {
    const blockerMap: Record<number, ProjectItem[]> = {}

    await Promise.all(
      items.value.map(async (item) => {
        try {
          const response = await api.get<ProjectItem[]>(`/project-items/${item.id}/blockers/`)
          if (response.data.length > 0) {
            blockerMap[item.id] = response.data
          }
        } catch {
          // Non-critical — skip blocker info for this item
        }
      })
    )

    itemBlockers.value = blockerMap
    logger.debug('item_blockers_fetched', { blocked_count: Object.keys(blockerMap).length })
  }

  async function fetchItemDetail(id: number) {
    const response = await api.get<ProjectItemDetail>(`/project-items/${id}/`)
    return response.data
  }

  // --- Dependencies ---

  async function addDependency(itemId: number, input: ProjectItemDependencyCreate) {
    error.value = null
    try {
      const response = await api.post<ProjectItemDetail>(`/project-items/${itemId}/dependencies/`, input)
      logger.info('dependency_added', { item_id: itemId, depends_on: input.depends_on_id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('dependency_add_failed', {
        item_id: itemId,
        detail: apiError.detail,
        status: apiError.status,
      })
      throw apiError
    }
  }

  async function removeDependency(itemId: number, depId: number) {
    error.value = null
    try {
      await api.delete(`/project-items/${itemId}/dependencies/${depId}/`)
      logger.info('dependency_removed', { item_id: itemId, dep_id: depId })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('dependency_remove_failed', {
        item_id: itemId,
        detail: apiError.detail,
        status: apiError.status,
      })
      throw apiError
    }
  }

  async function getBlockers(itemId: number) {
    try {
      const response = await api.get<ProjectItem[]>(`/project-items/${itemId}/blockers/`)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      logger.error('blockers_fetch_failed', {
        item_id: itemId,
        detail: apiError.detail,
        status: apiError.status,
      })
      throw apiError
    }
  }

  // --- Membership ---

  async function addToProject(itemId: number, input: ProjectItemMembershipCreate) {
    error.value = null
    try {
      await api.post(`/project-items/${itemId}/projects/`, input)
      logger.info('item_added_to_project', { item_id: itemId, project_id: input.project_id })
      await fetchProjects()
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      throw apiError
    }
  }

  async function removeFromProject(itemId: number, projectId: number) {
    error.value = null
    try {
      await api.delete(`/project-items/${itemId}/projects/${projectId}/`)
      logger.info('item_removed_from_project', { item_id: itemId, project_id: projectId })
      await fetchProjects()
      if (selectedProjectId.value !== null) {
        await fetchItems(selectedProjectId.value)
      }
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      throw apiError
    }
  }

  // --- Search ---

  async function searchItems(query: string) {
    try {
      const response = await api.get<ProjectItem[]>('/project-items/search/', {
        params: { q: query },
      })
      logger.info('items_searched', { query, count: response.data.length })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      logger.error('items_search_failed', { query, detail: apiError.detail })
      throw apiError
    }
  }

  return {
    // Project state
    projects,
    selectedProjectId,
    loading,
    error,
    sortedProjects,
    selectedProject,
    // Item state
    items,
    itemsLoading,
    itemBlockers,
    sortedItems,
    // Actions
    clearError,
    fetchProjects,
    createProject,
    updateProject,
    removeProject,
    fetchItems,
    createItem,
    updateItem,
    removeItem,
    reorderItem,
    reorderItems,
    reorderProjects,
    completeItem,
    archiveItem,
    fetchItemBlockers,
    fetchItemDetail,
    addDependency,
    removeDependency,
    getBlockers,
    addToProject,
    removeFromProject,
    searchItems,
  }
})
