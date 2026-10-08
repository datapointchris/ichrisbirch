import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import IssueDetailPanel from '@/components/issues/IssueDetailPanel.vue'
import { useIssuesStore } from '@/stores/issues'
import type { Issue, IssueDetail } from '@/api/client'

const notify = vi.hoisted(() => vi.fn())

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: notify, close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

const issue: Issue = {
  id: 'id-907',
  number: 907,
  title: 'Route the new paths',
  description: 'The **router** order',
  acceptance: 'Every path resolves',
  repo: 'ichrisbirch',
  type: 'bug',
  status: 'in_progress',
  status_reason: null,
  priority: 1,
  effective_priority: 1,
  rank: 2,
  deferred_until_date: null,
  claimed_by: 'claude-code/abc',
  claim_expires_ts: '2026-10-08T06:00:00Z',
  initiative: null,
  parent: null,
  discovered_from: null,
  duplicate_of: null,
  labels: [],
  depends_on: [
    { id: 'id-906', number: 906, title: 'Rank renumber', status: 'completed' },
    { id: 'id-905', number: 905, title: 'Schema first', status: 'open' },
  ],
  blocks: [],
  child_count: 0,
  open_child_count: 0,
  comment_count: 1,
  is_blocked: true,
  is_ready: false,
  created_ts: '2026-10-01T12:00:00Z',
  updated_ts: '2026-10-01T12:00:00Z',
  closed_ts: null,
}

const detail: IssueDetail = {
  ...issue,
  children: [],
  comments: [{ id: 'c1', issue_id: 'id-907', body: 'Root cause: the router order', author: null, created_ts: '2026-10-07T12:00:00Z' }],
}

function mountPanel(withDetail: IssueDetail | null = detail) {
  return mount(IssueDetailPanel, {
    props: { issue, detail: withDetail },
    global: {
      plugins: [
        createTestingPinia({
          initialState: { auth: { user: { name: 'Chris' } } },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('IssueDetailPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the description and the done-when as markdown', () => {
    const wrapper = mountPanel()
    expect(wrapper.html()).toContain('<strong>router</strong>')
    expect(wrapper.text()).toContain('Every path resolves')
  })

  it('names who holds the claim and until when', () => {
    expect(mountPanel().text()).toContain('claude-code/abc until formatted:2026-10-08T06:00:00Z')
  })

  it('strikes a dependency that is already closed', () => {
    const dependencies = mountPanel().findAll('[data-testid="issue-dependency"]')
    expect(dependencies[0]!.classes()).toContain('issues__link--closed')
    expect(dependencies[1]!.classes()).not.toContain('issues__link--closed')
  })

  it('labels an unsigned comment rather than leaving the author blank', () => {
    expect(mountPanel().find('[data-testid="issue-comment"]').text()).toContain('unsigned')
  })

  it('says it is loading until the detail arrives', () => {
    expect(mountPanel(null).text()).toContain('Loading...')
  })

  it('waits on a typed issue number', async () => {
    const wrapper = mountPanel()
    await wrapper.find('[data-testid="issue-dependency-input"]').setValue('#812')
    await wrapper.find('[data-testid="issue-dependency-add"]').trigger('submit')
    expect(useIssuesStore().addDependency).toHaveBeenCalledWith(issue, 812)
  })

  it('refuses a dependency that is not a number before asking the API', async () => {
    const wrapper = mountPanel()
    await wrapper.find('[data-testid="issue-dependency-input"]').setValue('router')
    await wrapper.find('.issues__inline-form').trigger('submit')
    expect(useIssuesStore().addDependency).not.toHaveBeenCalled()
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('not an issue number'), 'error')
  })

  it('signs a comment with the signed-in user', async () => {
    const wrapper = mountPanel()
    await wrapper.find('[data-testid="issue-comment-input"]').setValue('Found it')
    await wrapper.find('.issues__comment-form').trigger('submit')
    expect(useIssuesStore().addComment).toHaveBeenCalledWith(issue, 'Found it', 'Chris')
  })

  it('removes a dependency by the issue it names', async () => {
    const wrapper = mountPanel()
    await wrapper.findAll('[data-testid="issue-dependency-remove"]')[1]!.trigger('click')
    expect(useIssuesStore().removeDependency).toHaveBeenCalledWith(issue, issue.depends_on[1])
  })
})
