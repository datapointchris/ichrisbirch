import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CancelIssueModal from '@/components/issues/CancelIssueModal.vue'
import type { Issue } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: vi.fn(), close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const issue = { id: 'id-906', number: 906, title: 'Rank renumber' } as Issue

function mountModal() {
  return mount(CancelIssueModal, {
    props: { visible: true, issue },
    global: {
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible', 'focusRef'],
        },
      },
    },
  })
}

describe('CancelIssueModal', () => {
  it('sends the reason it was given', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="issue-cancel-reason-input"]').setValue('  decided in the design review ')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('cancel')![0]![0]).toEqual({ status_reason: 'decided in the design review' })
  })

  it('takes the issue it duplicates in place of a reason', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="issue-duplicate-of-input"]').setValue('#812')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('cancel')![0]![0]).toEqual({ duplicate_of: 812 })
  })

  it('sends nothing with neither a reason nor a duplicate', async () => {
    const wrapper = mountModal()
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('cancel')).toBeFalsy()
  })

  it('refuses a duplicate that is not an issue number', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-testid="issue-cancel-reason-input"]').setValue('superseded')
    await wrapper.find('[data-testid="issue-duplicate-of-input"]').setValue('the other one')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('cancel')).toBeFalsy()
  })
})
