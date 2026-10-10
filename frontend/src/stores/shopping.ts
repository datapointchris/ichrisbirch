import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import { todayKey } from '@/composables/calendarDay'
import type {
  ShoppingItem,
  ShoppingItemCreate,
  ShoppingItemRankMove,
  ShoppingItemUpdate,
  ShoppingPurchase,
  ShoppingSection,
} from '@/api/client'

const logger = createLogger('ShoppingStore')

/** The key Unsorted goes by wherever a section id would be. */
export const UNSORTED_KEY = 'unsorted'

const BUY_AGAIN_SHOWN = 8
const SUGGESTIONS_SHOWN = 6

export interface ShoppingGroup {
  key: string
  section: ShoppingSection | null
  items: ShoppingItem[]
}

function byRank<T extends { rank: number }>(a: T, b: T): number {
  return a.rank - b.rank
}

/** Unsorted, then every section in rank order, each holding its items in rank order. */
export function groupBySection(sections: ShoppingSection[], items: ShoppingItem[]): ShoppingGroup[] {
  const ordered = [...items].sort(byRank)
  const unsorted: ShoppingGroup = { key: UNSORTED_KEY, section: null, items: ordered.filter((item) => item.section_id === null) }
  const groups = [...sections].sort(byRank).map((section) => ({
    key: section.id,
    section,
    items: ordered.filter((item) => item.section_id === section.id),
  }))
  return [unsorted, ...groups]
}

/** What was bought most often and is not on the list now. */
export function buyAgainOf(catalog: ShoppingItem[]): ShoppingItem[] {
  return catalog
    .filter((item) => !item.is_needed && item.purchase_count > 0)
    .sort((a, b) => b.purchase_count - a.purchase_count || (b.last_purchased_ts ?? '').localeCompare(a.last_purchased_ts ?? ''))
    .slice(0, BUY_AGAIN_SHOWN)
}

/** Catalog names containing what was typed, those starting with it first. */
export function suggestionsFor(typed: string, catalog: ShoppingItem[]): ShoppingItem[] {
  const folded = typed.trim().toLowerCase()
  if (!folded) return []
  return catalog
    .filter((item) => item.name.toLowerCase().includes(folded))
    .sort((a, b) => {
      const aStarts = a.name.toLowerCase().startsWith(folded)
      const bStarts = b.name.toLowerCase().startsWith(folded)
      return aStarts === bStarts ? a.name.localeCompare(b.name) : aStarts ? -1 : 1
    })
    .slice(0, SUGGESTIONS_SHOWN)
}

/** Where a row dropped at `index` of `list` goes: after the row above it, else before the row below. */
export function itemMoveFor(section: string | null, list: ShoppingItem[], index: number): ShoppingItemRankMove {
  const above = list[index - 1]
  if (above) return { section, after: above.id }
  const below = list[index + 1]
  if (below) return { section, before: below.id }
  return { section }
}

/** The same for a section header, which always has a neighbor once there are two sections. */
export function sectionMoveFor(list: ShoppingSection[], index: number): { after: string } | { before: string } | null {
  const above = list[index - 1]
  if (above) return { after: above.id }
  const below = list[index + 1]
  if (below) return { before: below.id }
  return null
}

function wrapError(e: unknown): ApiError {
  return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
}

export const useShoppingStore = defineStore('shopping', () => {
  const sections = ref<ShoppingSection[]>([])
  // The whole catalog: what is on the list and what is not.
  const catalog = ref<ShoppingItem[]>([])
  const boughtToday = ref<ShoppingPurchase[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const needed = computed(() => catalog.value.filter((item) => item.is_needed))
  const groups = computed(() => groupBySection(sections.value, needed.value))
  const buyAgain = computed(() => buyAgainOf(catalog.value))

  function fail(event: string, e: unknown, context: Record<string, unknown> = {}): ApiError {
    const apiError = wrapError(e)
    error.value = apiError
    logger.error(event, { ...context, detail: apiError.detail, status: apiError.status })
    return apiError
  }

  function keep(item: ShoppingItem) {
    const index = catalog.value.findIndex((row) => row.id === item.id)
    if (index === -1) catalog.value.push(item)
    else catalog.value[index] = item
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const [sectionRows, itemRows, purchaseRows] = await Promise.all([
        api.get<ShoppingSection[]>('/shopping/sections/'),
        api.get<ShoppingItem[]>('/shopping/items/', { params: { status: 'all' } }),
        api.get<ShoppingPurchase[]>('/shopping/purchases/', { params: { start_date: todayKey() } }),
      ])
      sections.value = sectionRows.data
      catalog.value = itemRows.data
      boughtToday.value = purchaseRows.data
      logger.info('shopping_fetched', { sections: sectionRows.data.length, items: itemRows.data.length })
    } catch (e) {
      throw fail('shopping_fetch_failed', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchItems() {
    const response = await api.get<ShoppingItem[]>('/shopping/items/', { params: { status: 'all' } })
    catalog.value = response.data
  }

  async function addItem(input: ShoppingItemCreate) {
    error.value = null
    try {
      const response = await api.post<ShoppingItem>('/shopping/items/', input)
      keep(response.data)
      logger.info('shopping_item_added', { name: response.data.name, created: response.status === 201 })
      return response.data
    } catch (e) {
      throw fail('shopping_item_add_failed', e, { name: input.name })
    }
  }

  async function updateItem(id: string, input: ShoppingItemUpdate) {
    error.value = null
    try {
      const response = await api.patch<ShoppingItem>(`/shopping/items/${id}/`, input)
      keep(response.data)
      logger.info('shopping_item_updated', { id })
      return response.data
    } catch (e) {
      throw fail('shopping_item_update_failed', e, { id })
    }
  }

  async function deleteItem(id: string) {
    error.value = null
    try {
      await api.delete(`/shopping/items/${id}/`)
      catalog.value = catalog.value.filter((item) => item.id !== id)
      logger.info('shopping_item_deleted', { id })
    } catch (e) {
      throw fail('shopping_item_delete_failed', e, { id })
    }
  }

  /** Persist a drag. The page has already moved the row, so a failure re-reads the list to put it back. */
  async function moveItem(id: string, move: ShoppingItemRankMove) {
    error.value = null
    try {
      const response = await api.post<ShoppingItem>(`/shopping/items/${id}/rank/`, move)
      keep(response.data)
      logger.info('shopping_item_moved', { id, section: move.section })
      return response.data
    } catch (e) {
      const apiError = fail('shopping_item_move_failed', e, { id })
      await fetchItems().catch(() => logger.warning('shopping_items_refetch_failed'))
      throw apiError
    }
  }

  /** Take the item off the list at once and record the purchase; put it back if the record fails. */
  async function checkOff(item: ShoppingItem) {
    error.value = null
    keep({ ...item, is_needed: false })
    try {
      const response = await api.post<ShoppingPurchase>(`/shopping/items/${item.id}/purchases/`)
      boughtToday.value.unshift(response.data)
      keep({
        ...item,
        is_needed: false,
        note: null,
        purchase_count: item.purchase_count + 1,
        last_purchased_ts: response.data.purchased_ts,
      })
      logger.info('shopping_item_checked_off', { name: item.name })
      return response.data
    } catch (e) {
      keep(item)
      throw fail('shopping_check_off_failed', e, { name: item.name })
    }
  }

  /** Delete the purchase, which puts its item back on the list. */
  async function undoPurchase(purchase: ShoppingPurchase) {
    error.value = null
    try {
      await api.delete(`/shopping/purchases/${purchase.id}/`)
      boughtToday.value = boughtToday.value.filter((row) => row.id !== purchase.id)
      if (purchase.item_id) {
        const response = await api.get<ShoppingItem>(`/shopping/items/${purchase.item_id}/`)
        keep(response.data)
      }
      logger.info('shopping_purchase_undone', { name: purchase.item_name })
    } catch (e) {
      throw fail('shopping_purchase_undo_failed', e, { name: purchase.item_name })
    }
  }

  async function createSection(name: string) {
    error.value = null
    try {
      const response = await api.post<ShoppingSection>('/shopping/sections/', { name })
      sections.value.push(response.data)
      logger.info('shopping_section_created', { name })
      return response.data
    } catch (e) {
      throw fail('shopping_section_create_failed', e, { name })
    }
  }

  async function renameSection(id: string, name: string) {
    error.value = null
    try {
      const response = await api.patch<ShoppingSection>(`/shopping/sections/${id}/`, { name })
      sections.value = sections.value.map((section) => (section.id === id ? response.data : section))
      for (const item of catalog.value) {
        if (item.section_id === id) item.section_name = response.data.name
      }
      logger.info('shopping_section_renamed', { id, name })
      return response.data
    } catch (e) {
      throw fail('shopping_section_rename_failed', e, { id })
    }
  }

  async function deleteSection(id: string) {
    error.value = null
    try {
      await api.delete(`/shopping/sections/${id}/`)
      sections.value = sections.value.filter((section) => section.id !== id)
      for (const item of catalog.value) {
        if (item.section_id === id) {
          item.section_id = null
          item.section_name = null
        }
      }
      logger.info('shopping_section_deleted', { id })
    } catch (e) {
      throw fail('shopping_section_delete_failed', e, { id })
    }
  }

  async function moveSection(id: string, neighbor: { before: string } | { after: string }) {
    error.value = null
    try {
      const response = await api.post<ShoppingSection>(`/shopping/sections/${id}/rank/`, neighbor)
      sections.value = sections.value.map((section) => (section.id === id ? response.data : section))
      logger.info('shopping_section_moved', { id })
      return response.data
    } catch (e) {
      const apiError = fail('shopping_section_move_failed', e, { id })
      const response = await api.get<ShoppingSection[]>('/shopping/sections/').catch(() => null)
      if (response) sections.value = response.data
      throw apiError
    }
  }

  return {
    sections,
    catalog,
    boughtToday,
    loading,
    error,
    needed,
    groups,
    buyAgain,
    fetchAll,
    addItem,
    updateItem,
    deleteItem,
    moveItem,
    checkOff,
    undoPurchase,
    createSection,
    renameSection,
    deleteSection,
    moveSection,
  }
})
