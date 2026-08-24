import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AddEditEventModal from '@/components/events/AddEditEventModal.vue'
import type { Event } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: vi.fn(), close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

function mountModal(editData: Event | null = null) {
  return mount(AddEditEventModal, {
    props: { visible: true, editData },
    global: {
      stubs: {
        // The wrapper renders its default slot with the handlers the form needs.
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible', 'focusRef'],
        },
      },
    },
  })
}

async function fillAndSubmit(wrapper: ReturnType<typeof mountModal>) {
  await wrapper.find('[data-testid="event-name-input"]').setValue('Concert')
  await wrapper.find('[data-testid="event-date-input"]').setValue('2026-09-28T19:00')
  await wrapper.find('[data-testid="event-venue-input"]').setValue('Arena')
  await wrapper.find('form').trigger('submit')
}

describe('AddEditEventModal timezone', () => {
  it('defaults the zone to the reader’s own', async () => {
    const wrapper = mountModal()
    await fillAndSubmit(wrapper)

    const [payload] = wrapper.emitted('create')![0] as [Record<string, unknown>]
    expect(payload.timezone).toBe(browserTimezone)
  })

  it('sends the wall clock unchanged, with no offset attached', async () => {
    const wrapper = mountModal()
    await fillAndSubmit(wrapper)

    const [payload] = wrapper.emitted('create')![0] as [Record<string, unknown>]
    expect(payload.date).toBe('2026-09-28T19:00')
  })

  it('carries the event’s own zone into an edit rather than the reader’s', async () => {
    const existing: Event = {
      id: 7,
      name: 'Conference',
      date: '2026-09-28T09:00:00',
      timezone: 'Asia/Tokyo',
      venue: 'Convention Center',
      cost: 0,
      attending: true,
    }
    // The watch fires on the visible transition, which is how the parent opens it —
    // mounting already-open leaves the form empty and the submit guard rejects it.
    const wrapper = mount(AddEditEventModal, {
      props: { visible: false, editData: existing },
      global: {
        stubs: {
          AddEditModal: {
            template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
            props: ['visible', 'focusRef'],
          },
        },
      },
    })
    await wrapper.setProps({ visible: true })
    await wrapper.find('form').trigger('submit')

    const [, payload] = wrapper.emitted('update')![0] as [number, Record<string, unknown>]
    expect(payload.timezone).toBe('Asia/Tokyo')
  })
})
