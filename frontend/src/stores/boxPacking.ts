import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type { Box, BoxCreate, BoxUpdate, BoxItem, BoxItemCreate, BoxSize } from '@/api/client'

export interface BoxSearchResult {
  box: Box
  item: BoxItem
}

const logger = createLogger('BoxPackingStore')

type SortField = 'number' | 'name' | 'size' | 'item_count' | 'essential' | 'warm' | 'liquid'
type ViewMode = 'block' | 'compact'

export const BOX_SIZES: BoxSize[] = ['Bag', 'Book', 'Large', 'Medium', 'Misc', 'Monitor', 'Sixteen', 'Small', 'UhaulSmall']

export const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: 'number', label: 'Number' },
  { value: 'name', label: 'Name' },
  { value: 'size', label: 'Size' },
  { value: 'item_count', label: 'Item Count' },
  { value: 'essential', label: 'Essential' },
  { value: 'warm', label: 'Warm' },
  { value: 'liquid', label: 'Liquid' },
]

export type { SortField, ViewMode }

function compareBySortField(a: Box, b: Box, field: SortField): number {
  switch (field) {
    case 'number':
      return (a.number ?? 0) - (b.number ?? 0)
    case 'name':
      return a.name.localeCompare(b.name)
    case 'size':
      return a.size.localeCompare(b.size)
    case 'item_count':
      return a.items.length - b.items.length
    case 'essential':
      return Number(b.essential) - Number(a.essential)
    case 'warm':
      return Number(b.warm) - Number(a.warm)
    case 'liquid':
      return Number(b.liquid) - Number(a.liquid)
  }
}

export const useBoxPackingStore = defineStore('boxPacking', () => {
  const boxes = ref<Box[]>([])
  const orphans = ref<BoxItem[]>([])
  const searchResults = ref<BoxSearchResult[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const sortField1 = ref<SortField>('number')
  const sortField2 = ref<SortField | ''>('')
  const viewMode = ref<ViewMode>((localStorage.getItem('boxPacking.viewMode') as ViewMode) || 'block')

  const sortedBoxes = computed(() => {
    const sorted = [...boxes.value]
    sorted.sort((a, b) => {
      const primary = compareBySortField(a, b, sortField1.value)
      if (primary !== 0 || !sortField2.value) return primary
      return compareBySortField(a, b, sortField2.value)
    })
    return sorted
  })

  function clearError() {
    error.value = null
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
    localStorage.setItem('boxPacking.viewMode', mode)
  }

  function setSortFields(s1: SortField, s2: SortField | '') {
    sortField1.value = s1
    sortField2.value = s2
  }

  // --- Boxes ---

  async function fetchBoxes() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Box[]>('/box-packing/boxes/')
      boxes.value = response.data
      logger.info('boxes_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('boxes_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function fetchBox(id: number) {
    error.value = null
    try {
      const response = await api.get<Box>(`/box-packing/boxes/${id}/`)
      const index = boxes.value.findIndex((b) => b.id === id)
      if (index !== -1) {
        boxes.value[index] = response.data
      }
      logger.info('box_fetched', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('box_fetch_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function createBox(input: BoxCreate) {
    error.value = null
    try {
      const response = await api.post<Box>('/box-packing/boxes/', input)
      boxes.value.push(response.data)
      logger.info('box_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('box_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function updateBox(id: number, input: BoxUpdate) {
    error.value = null
    try {
      const response = await api.patch<Box>(`/box-packing/boxes/${id}/`, input)
      const index = boxes.value.findIndex((b) => b.id === id)
      if (index !== -1) {
        boxes.value[index] = response.data
      }
      logger.info('box_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('box_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function deleteBox(id: number) {
    error.value = null
    try {
      await api.delete(`/box-packing/boxes/${id}/`)
      boxes.value = boxes.value.filter((b) => b.id !== id)
      logger.info('box_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('box_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  // --- Items ---

  async function createItem(input: BoxItemCreate) {
    error.value = null
    try {
      const response = await api.post<BoxItem>('/box-packing/items/', input)
      logger.info('item_created', { id: response.data.id, name: response.data.name })
      // Re-fetch parent box to get updated derived attributes
      await fetchBox(input.box_id)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function deleteItem(id: number, boxId?: number) {
    error.value = null
    try {
      await api.delete(`/box-packing/items/${id}/`)
      logger.info('item_deleted', { id })
      // Re-fetch parent box to get updated derived attributes
      if (boxId) {
        await fetchBox(boxId)
      }
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function orphanItem(id: number, boxId: number) {
    error.value = null
    try {
      const response = await api.patch<BoxItem>(`/box-packing/items/${id}/`, { box_id: null })
      logger.info('item_orphaned', { id })
      // Re-fetch the box the item was removed from
      await fetchBox(boxId)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('item_orphan_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function assignOrphanToBox(itemId: number, boxId: number) {
    error.value = null
    try {
      const response = await api.patch<BoxItem>(`/box-packing/items/${itemId}/`, { box_id: boxId })
      orphans.value = orphans.value.filter((o) => o.id !== itemId)
      logger.info('orphan_assigned', { itemId, boxId })
      // Re-fetch target box to get updated derived attributes
      await fetchBox(boxId)
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('orphan_assign_failed', { itemId, boxId, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  // --- Orphans ---

  async function fetchOrphans() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<BoxItem[]>('/box-packing/items/orphans/')
      orphans.value = response.data
      logger.info('orphans_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('orphans_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function deleteOrphan(id: number) {
    error.value = null
    try {
      await api.delete(`/box-packing/items/${id}/`)
      orphans.value = orphans.value.filter((o) => o.id !== id)
      logger.info('orphan_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('orphan_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  // --- Search ---

  async function search(query: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<[Box, BoxItem][]>('/box-packing/search/', { params: { q: query } })
      searchResults.value = response.data.map(([box, item]) => ({ box, item }))
      logger.info('search_completed', { query, count: searchResults.value.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('search_failed', { query, detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  return {
    boxes,
    orphans,
    searchResults,
    loading,
    error,
    sortField1,
    sortField2,
    viewMode,
    sortedBoxes,
    clearError,
    setViewMode,
    setSortFields,
    fetchBoxes,
    fetchBox,
    createBox,
    updateBox,
    deleteBox,
    createItem,
    deleteItem,
    orphanItem,
    assignOrphanToBox,
    fetchOrphans,
    deleteOrphan,
    search,
  }
})
