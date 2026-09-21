import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import WidgetDurations from '@/components/dashboard/WidgetDurations.vue'
import type { Duration } from '@/api/client'

vi.mock('@/composables/displayZone', () => ({
  displayZone: () => 'America/New_York',
}))

function startedOn(start_date: string): Duration {
  return { id: 1, name: 'Running', start_date, duration_notes: [] }
}

function elapsedFor(duration: Duration): string {
  const wrapper = mount(WidgetDurations, {
    global: {
      plugins: [createTestingPinia({ initialState: { durations: { durations: [duration] } }, stubActions: true, createSpy: vi.fn })],
    },
  })
  return wrapper.find('.widget-list__meta').text()
}

describe('WidgetDurations', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // 20:30 on the 20th in New York is already the 21st in UTC.
    vi.setSystemTime(new Date('2026-09-21T00:30:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('counts a duration started today in the user zone as today, whatever the UTC day', () => {
    expect(elapsedFor(startedOn('2026-09-20'))).toBe('Today')
  })

  it('counts whole calendar days back to the start day', () => {
    expect(elapsedFor(startedOn('2026-09-10'))).toBe('10d')
  })
})
