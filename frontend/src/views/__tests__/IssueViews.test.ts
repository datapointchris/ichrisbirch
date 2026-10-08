// Component integration tests for IssueInitiativesView and IssueLabelsView.
// E2E counterpart: e2e/issues.spec.ts (smoke only — each page loads)
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import IssueInitiativesView from '../IssueInitiativesView.vue'
import IssueLabelsView from '../IssueLabelsView.vue'
import { useIssueInitiativesStore } from '@/stores/issueInitiatives'
import { useIssueLabelsStore } from '@/stores/issueLabels'
import type { Initiative, IssueLabel } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: vi.fn(), close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const RouterLink = {
  props: ['to'],
  template: '<a :data-to="JSON.stringify(to)"><slot /></a>',
}

function linkTarget(element: { attributes: (name: string) => string | undefined }) {
  return JSON.parse(element.attributes('data-to')!)
}

function makeInitiative(overrides: Partial<Initiative> = {}): Initiative {
  return {
    id: 'init-1',
    name: 'Ship the tracker',
    description: null,
    status: 'active',
    status_reason: null,
    priority: 2,
    position: 0,
    created_ts: '2026-10-01T12:00:00Z',
    closed_ts: null,
    issue_count: 3,
    open_count: 2,
    completed_count: 1,
    canceled_count: 0,
    repos: ['ichrisbirch', 'dotfiles'],
    ...overrides,
  }
}

function mountInitiatives(items: Initiative[], statusFilter = 'active') {
  return mount(IssueInitiativesView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            issueInitiatives: { items, loading: false, error: null, statusFilter },
            issues: { vocabulary: { priorities: [{ value: 2, name: 'high' }], labels: [] } },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: { AppSubnav: true, NeuSelect: true, AddEditInitiativeModal: true, DropInitiativeModal: true, RouterLink },
    },
  })
}

describe('IssueInitiativesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('links an active initiative to the work left in it', () => {
    const link = mountInitiatives([makeInitiative()]).find('[data-testid="initiative-issues-link"]')
    expect(linkTarget(link)).toEqual({ path: '/issues', query: { initiative: 'Ship the tracker' } })
  })

  it('links a finished initiative to every issue it held', () => {
    const finished = makeInitiative({ status: 'completed', closed_ts: '2026-10-06T12:00:00Z' })
    const link = mountInitiatives([finished], 'all').find('[data-testid="initiative-issues-link"]')
    expect(linkTarget(link)).toEqual({ path: '/issues', query: { initiative: 'Ship the tracker', status: 'all' } })
  })

  it('names the priority and the repos the work touched', () => {
    const row = mountInitiatives([makeInitiative()]).find('[data-testid="initiative-item"]')
    expect(row.text()).toContain('high')
    expect(row.text()).toContain('ichrisbirch, dotfiles')
    expect(row.classes()).toContain('issue--p2')
  })

  it('offers reopen in place of complete and drop once finished', () => {
    const wrapper = mountInitiatives([makeInitiative({ status: 'dropped', status_reason: 'superseded' })], 'all')
    expect(wrapper.find('[data-testid="initiative-reopen-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="initiative-complete-button"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="initiative-drop-button"]').exists()).toBe(false)
  })

  it('drops an initiative with the reason the modal collected', async () => {
    const initiative = makeInitiative()
    const wrapper = mountInitiatives([initiative])
    await wrapper.find('[data-testid="initiative-drop-button"]').trigger('click')
    wrapper.findComponent({ name: 'DropInitiativeModal' }).vm.$emit('drop', 'the outcome moved elsewhere')
    expect(useIssueInitiativesStore().setStatus).toHaveBeenCalledWith(initiative, 'dropped', 'the outcome moved elsewhere')
  })

  it('names the status filter in an empty list', () => {
    expect(mountInitiatives([], 'completed').find('[data-testid="initiative-empty"]').text()).toBe('No completed initiatives.')
  })
})

const labels: IssueLabel[] = [
  { slug: 'area-cli', group_slug: 'area', description: 'The Go client', open_issue_count: 4 },
  { slug: 'needs-design', group_slug: null, description: null, open_issue_count: 0 },
]

function mountLabels(items: IssueLabel[] = labels) {
  return mount(IssueLabelsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: { issueLabels: { items, loading: false, error: null } },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: { AppSubnav: true, AddEditIssueLabelModal: true, RouterLink },
    },
  })
}

describe('IssueLabelsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('links each label to the issues carrying it', () => {
    const link = mountLabels().findAll('[data-testid="issue-label-issues-link"]')[0]!
    expect(linkTarget(link)).toEqual({ path: '/issues', query: { label: 'area-cli' } })
  })

  it('marks a label outside any group', () => {
    const rows = mountLabels().findAll('[data-testid="issue-label-item"]')
    expect(rows[1]!.text()).toContain('—')
  })

  it('deletes a label by its slug', async () => {
    const wrapper = mountLabels()
    await wrapper.findAll('[data-testid="issue-label-delete-button"]')[1]!.trigger('click')
    expect(useIssueLabelsStore().remove).toHaveBeenCalledWith('needs-design')
  })
})
