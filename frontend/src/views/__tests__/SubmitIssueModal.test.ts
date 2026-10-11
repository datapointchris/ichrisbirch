import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import SubmitIssueModal from '@/components/SubmitIssueModal.vue'
import { useIssuesStore } from '@/stores/issues'

const notify = vi.hoisted(() => vi.fn())

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: notify, close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

function mountModal() {
  const wrapper = mount(SubmitIssueModal, {
    props: { visible: true },
    global: {
      plugins: [createTestingPinia({ stubActions: true, createSpy: vi.fn })],
      stubs: { teleport: true },
    },
  })
  const issues = useIssuesStore()
  vi.mocked(issues.create).mockResolvedValue({ number: 939 } as Awaited<ReturnType<typeof issues.create>>)
  return { wrapper, issues }
}

describe('SubmitIssueModal', () => {
  it('files into triage on this repo, carrying the page it was filed from', async () => {
    const { wrapper, issues } = mountModal()
    await wrapper.find('[data-testid="submit-issue-title-input"]').setValue('  Chart legend overlaps ')
    await wrapper.find('[data-testid="submit-issue-description-input"]').setValue('The legend covers the last bar.')
    await wrapper.find('form').trigger('submit')

    expect(issues.create).toHaveBeenCalledOnce()
    const filed = vi.mocked(issues.create).mock.calls[0]![0]
    expect(filed).toMatchObject({ title: 'Chart legend overlaps', repo: 'ichrisbirch', status: 'triage' })
    expect(filed).not.toHaveProperty('type')
    expect(filed.description).toContain('The legend covers the last bar.')
    expect(filed.description).toContain(window.location.href)
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('filed'), 'success')
  })

  it('sends the type that was chosen', async () => {
    const { wrapper, issues } = mountModal()
    await wrapper.find('[data-testid="submit-issue-title-input"]').setValue('Nav buttons do nothing')
    await wrapper.find('[data-testid="submit-issue-type-bug"]').setValue(true)
    await wrapper.find('form').trigger('submit')

    expect(vi.mocked(issues.create).mock.calls[0]![0]).toMatchObject({ type: 'bug', status: 'triage' })
  })
})
