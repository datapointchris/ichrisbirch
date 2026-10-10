import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import WidgetEvents from '../WidgetEvents.vue'
import type { Event } from '@/api/client'
import { addDays, todayKey } from '@/composables/calendarDay'
import { displayZone } from '@/composables/displayZone'

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

// Readings on today's calendar in the display zone, so they never rot as the clock moves.
function eventOn(id: number, name: string, day: string, time: string): Event {
  return { id, name, date: `${day}T${time}`, timezone: displayZone(), venue: 'V', cost: 0, attending: false }
}

function listedNames(events: Event[]): string[] {
  const wrapper = mount(WidgetEvents, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: { events: { events, loading: false, error: null } },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
  return wrapper.findAll('.widget-list__name').map((node) => node.text())
}

describe('WidgetEvents', () => {
  it('lists today onward, so an event this morning stays and yesterday goes', () => {
    const today = todayKey()
    const names = listedNames([
      eventOn(1, 'yesterday night', addDays(today, -1), '23:59:00'),
      eventOn(2, 'this morning', today, '00:01:00'),
    ])

    expect(names).toEqual(['this morning'])
  })

  it('orders soonest first, with an event already over today ahead of next week', () => {
    const today = todayKey()
    const names = listedNames([eventOn(1, 'next week', addDays(today, 7), '12:00:00'), eventOn(2, 'this morning', today, '00:01:00')])

    expect(names).toEqual(['this morning', 'next week'])
  })
})
