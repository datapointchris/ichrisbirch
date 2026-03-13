import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCountdownsStore } from '../countdowns'

describe('useCountdownsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty state', () => {
    const store = useCountdownsStore()
    expect(store.countdowns).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sorts countdowns by due_date', () => {
    const store = useCountdownsStore()
    store.countdowns = [
      { id: 1, name: 'Later', due_date: '2026-12-01' },
      { id: 2, name: 'Sooner', due_date: '2026-06-01' },
      { id: 3, name: 'Soonest', due_date: '2026-03-01' },
    ]
    expect(store.sortedCountdowns.map((c) => c.name)).toEqual(['Soonest', 'Sooner', 'Later'])
  })
})
