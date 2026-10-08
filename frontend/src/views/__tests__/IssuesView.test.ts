import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import IssuesView from '../IssuesView.vue'
import { useIssuesStore } from '@/stores/issues'
import type { Issue, IssueVocabulary } from '@/api/client'

const route = vi.hoisted(() => ({ query: {} as Record<string, string> }))

vi.mock('vue-router', () => ({ useRoute: () => route }))

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

function makeIssue(overrides: Partial<Issue>): Issue {
  return {
    id: `id-${overrides.number ?? 1}`,
    number: 1,
    title: 'An issue',
    description: null,
    acceptance: null,
    repo: 'ichrisbirch',
    type: 'task',
    status: 'open',
    status_reason: null,
    priority: 0,
    effective_priority: 0,
    rank: 1,
    deferred_until_date: null,
    claimed_by: null,
    claim_expires_ts: null,
    initiative: null,
    parent: null,
    discovered_from: null,
    duplicate_of: null,
    labels: [],
    depends_on: [],
    blocks: [],
    child_count: 0,
    open_child_count: 0,
    comment_count: 0,
    is_blocked: false,
    is_ready: true,
    created_ts: '2026-10-01T12:00:00Z',
    updated_ts: '2026-10-01T12:00:00Z',
    closed_ts: null,
    ...overrides,
  }
}

// The blocker sets no priority of its own and inherits urgent from the bug
// waiting on it; the two urgent rows can trade places, the others cannot.
const blocker = makeIssue({ number: 906, title: 'Rank renumber', effective_priority: 1, labels: ['area-api'] })
const bug = makeIssue({
  number: 907,
  title: 'Route the new paths',
  type: 'bug',
  priority: 1,
  effective_priority: 1,
  is_blocked: true,
  is_ready: false,
  depends_on: [{ id: 'id-906', number: 906, title: 'Rank renumber', status: 'open' }],
})
const claimed = makeIssue({ number: 908, status: 'in_progress', claimed_by: 'claude-code/abc', is_ready: false, open_child_count: 2 })
const triage = makeIssue({ number: 909, status: 'triage', is_ready: false })
const decision = makeIssue({ number: 910, type: 'decision', title: 'Pick a scheme' })
const done = makeIssue({ number: 911, status: 'completed', is_ready: false, closed_ts: '2026-10-05T12:00:00Z' })
const testIssues = [blocker, bug, claimed, triage, decision, done]

const vocabulary: IssueVocabulary = {
  statuses: ['triage', 'open', 'in_progress', 'completed', 'canceled'],
  types: ['bug', 'feature', 'task', 'chore', 'decision'],
  priorities: [
    { value: 0, name: 'none' },
    { value: 1, name: 'urgent' },
    { value: 2, name: 'high' },
    { value: 3, name: 'medium' },
    { value: 4, name: 'low' },
  ],
  initiative_statuses: ['active', 'completed', 'dropped'],
  labels: [{ slug: 'area-api', group_slug: 'area', description: null, open_issue_count: 1 }],
}

function createWrapper(state: Record<string, unknown> = {}) {
  return mount(IssuesView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            issues: {
              items: [],
              loading: false,
              error: null,
              vocabulary,
              statusFilter: 'unclosed',
              repoFilter: 'all',
              typeFilter: 'all',
              labelFilter: 'all',
              initiativeFilter: 'all',
              priorityFilter: 'all',
              search: '',
              lens: 'all',
              knownRepos: [],
              expandedId: null,
              detail: null,
              ...state,
            },
            issueInitiatives: { items: [], loading: false, error: null, statusFilter: 'active' },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: { template: '<div><slot /></div>' },
        AddEditIssueModal: true,
        CancelIssueModal: true,
        IssueDetailPanel: true,
        NeuSelect: true,
      },
    },
  })
}

function rowFor(wrapper: ReturnType<typeof createWrapper>, number: number) {
  const row = wrapper.findAll('[data-testid="issue-item"]').find((candidate) => candidate.text().startsWith(String(number)))
  expect(row, `no row for #${number}`).toBeTruthy()
  return row!
}

describe('IssuesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.query = {}
  })

  // --- Rendering ---

  it('reads the issues, the vocabulary and the initiatives on mount', () => {
    createWrapper()
    const store = useIssuesStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
    expect(store.fetchVocabulary).toHaveBeenCalledOnce()
  })

  it('renders one row per issue the lens keeps', () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(wrapper.findAll('[data-testid="issue-item"]')).toHaveLength(6)
  })

  it('counts every lens on its chip', () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(wrapper.find('[data-testid="issue-lens-ready"]').text()).toBe('Ready: 1')
    expect(wrapper.find('[data-testid="issue-lens-blocked"]').text()).toBe('Blocked: 1')
    expect(wrapper.find('[data-testid="issue-lens-decisions"]').text()).toBe('Decisions: 1')
  })

  // Decisions wait on a person and the agent queue leaves them out, so the
  // chip is the one place they surface.
  it('marks the decisions chip while a decision is waiting', () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(wrapper.find('[data-testid="issue-lens-decisions"]').classes()).toContain('issue-lens--attention')
    const none = createWrapper({ items: [blocker] })
    expect(none.find('[data-testid="issue-lens-decisions"]').classes()).not.toContain('issue-lens--attention')
  })

  it('stars a priority the issue inherited rather than set', () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(rowFor(wrapper, 906).text()).toContain('urgent*')
    expect(rowFor(wrapper, 907).text()).not.toContain('urgent*')
  })

  it('says why an issue waits', () => {
    const wrapper = createWrapper({ items: testIssues })
    const notes = (number: number) =>
      rowFor(wrapper, number)
        .findAll('[data-testid="issue-note"]')
        .map((note) => note.text())
    expect(notes(907)).toEqual(['waits on #906'])
    expect(notes(908)).toEqual(['claimed by claude-code/abc', '2 open children'])
  })

  it('colors each row by its effective priority', () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(rowFor(wrapper, 906).classes()).toContain('issue--p1')
    expect(rowFor(wrapper, 911).classes()).toContain('issue--closed')
  })

  it('names the narrowing behind an empty list', () => {
    const wrapper = createWrapper({ items: [], labelFilter: 'area-cli' })
    expect(wrapper.find('[data-testid="issue-empty"]').text()).toContain('label area-cli')
  })

  // --- Actions by status ---

  it('offers each status only the moves it can make', () => {
    const wrapper = createWrapper({ items: testIssues })
    const has = (number: number, action: string) => rowFor(wrapper, number).find(`[data-testid="issue-${action}-button"]`).exists()
    expect(has(909, 'accept')).toBe(true)
    expect(has(909, 'complete')).toBe(false)
    expect(has(906, 'start')).toBe(true)
    expect(has(908, 'release')).toBe(true)
    expect(has(908, 'start')).toBe(false)
    expect(has(911, 'reopen')).toBe(true)
    expect(has(911, 'cancel')).toBe(false)
  })

  it('accepts a triaged issue as open', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await rowFor(wrapper, 909).find('[data-testid="issue-accept-button"]').trigger('click')
    expect(useIssuesStore().setStatus).toHaveBeenCalledWith(triage, 'open')
  })

  it('cancels with what the cancel form collected', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await rowFor(wrapper, 906).find('[data-testid="issue-cancel-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'CancelIssueModal' })
    expect(modal.props('issue')).toEqual(blocker)

    modal.vm.$emit('cancel', { duplicate_of: 812 })
    await wrapper.vm.$nextTick()
    expect(useIssuesStore().setStatus).toHaveBeenCalledWith(blocker, 'canceled', { duplicate_of: 812 })
  })

  it('releases a claimed issue', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await rowFor(wrapper, 908).find('[data-testid="issue-release-button"]').trigger('click')
    expect(useIssuesStore().release).toHaveBeenCalledWith(claimed)
  })

  it('deletes an issue', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await rowFor(wrapper, 911).find('[data-testid="issue-delete-button"]').trigger('click')
    expect(useIssuesStore().remove).toHaveBeenCalledWith(done)
  })

  // --- Ordering ---

  // Priority decides order across priorities, so a move is offered only
  // between rows that share one.
  it('moves an issue only past a neighbor of the same priority', async () => {
    const wrapper = createWrapper({ items: testIssues })
    expect(rowFor(wrapper, 906).find('[data-testid="issue-move-up-button"]').exists()).toBe(false)
    expect(rowFor(wrapper, 906).find('[data-testid="issue-move-down-button"]').exists()).toBe(true)
    expect(rowFor(wrapper, 907).find('[data-testid="issue-move-down-button"]').exists()).toBe(false)

    await rowFor(wrapper, 907).find('[data-testid="issue-move-up-button"]').trigger('click')
    expect(useIssuesStore().move).toHaveBeenCalledWith(bug, { before: 906 })
  })

  // --- Detail and modals ---

  it('expands the detail panel under the open issue only', () => {
    const wrapper = createWrapper({ items: testIssues, expandedId: bug.id })
    const panels = wrapper.findAllComponents({ name: 'IssueDetailPanel' })
    expect(panels).toHaveLength(1)
    expect(panels[0]!.props('issue')).toEqual(bug)
  })

  it('opens the form empty to file an issue and filled to edit one', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await wrapper.find('[data-testid="issue-add-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'AddEditIssueModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()

    modal.vm.$emit('close')
    await rowFor(wrapper, 907).find('[data-testid="issue-edit-button"]').trigger('click')
    expect(wrapper.findComponent({ name: 'AddEditIssueModal' }).props('editData')).toEqual(bug)
  })

  it('switches the lens through the store', async () => {
    const wrapper = createWrapper({ items: testIssues })
    await wrapper.find('[data-testid="issue-lens-triage"]').trigger('click')
    expect(useIssuesStore().setLens).toHaveBeenCalledWith('triage')
  })

  // --- Links from the other pages ---

  it('replaces the filters with the ones a link names', () => {
    route.query = { initiative: 'Ship the tracker', status: 'all' }
    createWrapper()
    const store = useIssuesStore()
    expect(store.resetFilters).toHaveBeenCalledOnce()
    expect(store.setFilters).toHaveBeenCalledWith({ status: 'all', initiative: 'Ship the tracker' })
  })

  it('keeps the filters it was left with when the link names none', () => {
    createWrapper()
    expect(useIssuesStore().resetFilters).not.toHaveBeenCalled()
  })
})
