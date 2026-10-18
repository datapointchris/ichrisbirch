import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import {
  UNSORTED_KEY,
  buyAgainOf,
  groupBySection,
  itemMoveFor,
  purchasesByDay,
  sectionMoveFor,
  suggestionsFor,
  useShoppingStore,
} from '../shopping'
import { ApiError } from '@/api/errors'
import { dayStart } from '@/composables/calendarDay'
import type { ShoppingItem, ShoppingPurchase, ShoppingSection } from '@/api/client'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/composables/calendarDay', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/composables/calendarDay')>()),
  todayKey: () => '2026-10-10',
}))

import { api } from '@/api/client'
const mockApi = vi.mocked(api)

function section(id: string, rank: number): ShoppingSection {
  return { id, name: id, rank, created_ts: '2026-10-01T00:00:00Z' }
}

function item(name: string, overrides: Partial<ShoppingItem> = {}): ShoppingItem {
  return {
    id: name,
    name,
    note: null,
    section_id: null,
    section_name: null,
    rank: 1,
    is_needed: true,
    needed_ts: '2026-10-09T00:00:00Z',
    created_ts: '2026-10-01T00:00:00Z',
    purchase_count: 0,
    last_purchased_ts: null,
    ...overrides,
  }
}

function purchase(itemName: string, overrides: Partial<ShoppingPurchase> = {}): ShoppingPurchase {
  return {
    id: `p-${itemName}`,
    item_id: itemName,
    item_name: itemName,
    note: null,
    section_name: null,
    purchased_ts: '2026-10-10T15:00:00Z',
    ...overrides,
  }
}

const costco = section('Costco', 2)
const grocery = section('Grocery', 1)
const eggs = item('eggs', { section_id: 'Costco', section_name: 'Costco', rank: 3, note: '2 dozen' })
const bananas = item('bananas', { section_id: 'Grocery', section_name: 'Grocery', rank: 4 })
const yogurt = item('yogurt', { section_id: 'Grocery', section_name: 'Grocery', rank: 2 })
const tape = item('tape', { rank: 5 })
const milk = item('milk', { section_id: 'Grocery', section_name: 'Grocery', is_needed: false, purchase_count: 4 })
const coffee = item('coffee', { is_needed: false, purchase_count: 9 })
const catalog = [eggs, bananas, yogurt, tape, milk, coffee]

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

function seeded() {
  const store = useShoppingStore()
  store.sections = [costco, grocery]
  store.catalog = catalog.map((row) => ({ ...row }))
  return store
}

describe('groupBySection', () => {
  it('puts Unsorted first, then sections and their items in rank order', () => {
    const groups = groupBySection([costco, grocery], [eggs, bananas, yogurt, tape])
    expect(groups.map((group) => [group.key, group.items.map((row) => row.name)])).toEqual([
      [UNSORTED_KEY, ['tape']],
      ['Grocery', ['yogurt', 'bananas']],
      ['Costco', ['eggs']],
    ])
  })

  it('keeps an empty section, so it stays a drop target', () => {
    expect(groupBySection([costco], [])[1]).toMatchObject({ key: 'Costco', items: [] })
  })
})

describe('buyAgainOf', () => {
  it('offers what was bought and is off the list, most bought first', () => {
    expect(buyAgainOf(catalog).map((row) => row.name)).toEqual(['coffee', 'milk'])
  })
})

describe('suggestionsFor', () => {
  it('puts names starting with the typed text before names containing it', () => {
    const names = [item('peanut butter'), item('butter'), item('buttermilk')]
    expect(suggestionsFor('BUTTER', names).map((row) => row.name)).toEqual(['butter', 'buttermilk', 'peanut butter'])
  })

  it('suggests nothing for blank input', () => {
    expect(suggestionsFor('  ', catalog)).toEqual([])
  })
})

describe('itemMoveFor', () => {
  const list = [yogurt, eggs, bananas]

  it('places a row after the one above it', () => {
    expect(itemMoveFor('Grocery', list, 1)).toEqual({ section: 'Grocery', after: 'yogurt' })
  })

  it('places a row dropped first before the one below it', () => {
    expect(itemMoveFor('Grocery', list, 0)).toEqual({ section: 'Grocery', before: 'eggs' })
  })

  it('names only the section when the row is alone there', () => {
    expect(itemMoveFor(null, [eggs], 0)).toEqual({ section: null })
  })
})

describe('sectionMoveFor', () => {
  it('places a header after the one above, else before the one below', () => {
    expect(sectionMoveFor([grocery, costco], 1)).toEqual({ after: 'Grocery' })
    expect(sectionMoveFor([grocery, costco], 0)).toEqual({ before: 'Costco' })
    expect(sectionMoveFor([grocery], 0)).toBeNull()
  })
})

describe('purchasesByDay', () => {
  it('heads a check-off noticed days later under the day it was made', () => {
    const rows = [
      purchase('eggs', { purchased_ts: '2026-10-10T12:00:00Z' }),
      purchase('milk', { purchased_ts: '2026-10-09T12:00:00Z' }),
      purchase('nails', { purchased_ts: '2026-10-07T13:00:00Z' }),
      purchase('tape', { purchased_ts: '2026-10-07T12:00:00Z' }),
    ]

    const days = purchasesByDay(rows, '2026-10-10').map((day) => [day.label, day.purchases.map((row) => row.item_name)])

    expect(days).toEqual([
      ['Today', ['eggs']],
      ['Yesterday', ['milk']],
      ['Wednesday, Oct 7, 2026', ['nails', 'tape']],
    ])
  })
})

describe('useShoppingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('reads the sections, the whole catalog and the last week of purchases', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: [costco, grocery] })
      .mockResolvedValueOnce({ data: catalog })
      .mockResolvedValueOnce({ data: [purchase('milk')] })
    const store = useShoppingStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/shopping/items', { params: { status: 'all' } })
    expect(mockApi.get).toHaveBeenCalledWith('/shopping/purchases', { params: { since: dayStart('2026-10-04') } })
    expect(store.needed.map((row) => row.name)).toEqual(['eggs', 'bananas', 'yogurt', 'tape'])
    expect(store.recentPurchases).toHaveLength(1)
  })

  it('re-listing a known name replaces its catalog row rather than adding one', async () => {
    const store = seeded()
    mockApi.post.mockResolvedValueOnce({ status: 200, data: { ...milk, is_needed: true } })

    await store.addItem({ name: 'Milk' })

    expect(store.catalog.filter((row) => row.name === 'milk')).toHaveLength(1)
    expect(store.needed.map((row) => row.name)).toContain('milk')
  })

  it('takes a checked-off item off the list before the server answers', async () => {
    const store = seeded()
    const pending = deferred<{ data: ShoppingPurchase }>()
    mockApi.post.mockReturnValueOnce(pending.promise)

    const checking = store.checkOff(eggs)
    expect(store.needed.map((row) => row.name)).not.toContain('eggs')

    pending.resolve({ data: purchase('eggs', { note: '2 dozen' }) })
    await checking
    const after = store.catalog.find((row) => row.id === 'eggs')
    expect(after).toMatchObject({ is_needed: false, note: null, purchase_count: 1 })
    expect(store.recentPurchases[0]?.item_name).toBe('eggs')
  })

  it('puts a checked-off item back when the purchase is refused', async () => {
    const store = seeded()
    mockApi.post.mockRejectedValueOnce(new ApiError({ message: 'conflict', status: 409, detail: 'eggs is not on the list' }))

    await expect(store.checkOff(eggs)).rejects.toBeInstanceOf(ApiError)

    expect(store.needed.map((row) => row.name)).toContain('eggs')
    expect(store.error?.status).toBe(409)
  })

  it('undoing a purchase re-reads its item, which is back on the list', async () => {
    const store = seeded()
    store.recentPurchases = [purchase('milk')]
    mockApi.delete.mockResolvedValueOnce({})
    mockApi.get.mockResolvedValueOnce({ data: { ...milk, is_needed: true } })

    await store.undoPurchase(purchase('milk'))

    expect(mockApi.delete).toHaveBeenCalledWith('/shopping/purchases/p-milk')
    expect(store.recentPurchases).toEqual([])
    expect(store.needed.map((row) => row.name)).toContain('milk')
  })

  it('re-reads the catalog when a move is refused, so the dragged row returns', async () => {
    const store = seeded()
    mockApi.post.mockRejectedValueOnce(new ApiError({ message: 'bad', status: 422, detail: 'bananas is in Grocery' }))
    mockApi.get.mockResolvedValueOnce({ data: catalog })

    await expect(store.moveItem('eggs', { section: 'Costco', after: 'bananas' })).rejects.toBeInstanceOf(ApiError)

    expect(mockApi.get).toHaveBeenCalledWith('/shopping/items', { params: { status: 'all' } })
  })

  it('renaming a section renames it on its items', async () => {
    const store = seeded()
    mockApi.patch.mockResolvedValueOnce({ data: { ...grocery, name: 'Trader Joe’s' } })

    await store.renameSection('Grocery', 'Trader Joe’s')

    expect(store.catalog.find((row) => row.id === 'bananas')?.section_name).toBe('Trader Joe’s')
  })

  it('deleting a section leaves its items in Unsorted', async () => {
    const store = seeded()
    mockApi.delete.mockResolvedValueOnce({})

    await store.deleteSection('Grocery')

    const unsorted = store.groups.find((group) => group.key === UNSORTED_KEY)
    expect(unsorted?.items.map((row) => row.name)).toEqual(['yogurt', 'bananas', 'tape'])
    expect(store.sections.map((row) => row.id)).toEqual(['Costco'])
  })
})
