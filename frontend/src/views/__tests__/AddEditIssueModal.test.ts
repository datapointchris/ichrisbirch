import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AddEditIssueModal from '@/components/issues/AddEditIssueModal.vue'
import type { Initiative, Issue, IssueVocabulary } from '@/api/client'

const notify = vi.hoisted(() => vi.fn())

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: notify, close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const vocabulary: IssueVocabulary = {
  statuses: ['triage', 'open', 'in_progress', 'completed', 'canceled'],
  types: ['bug', 'feature', 'task', 'chore', 'decision'],
  priorities: [
    { value: 0, name: 'none' },
    { value: 1, name: 'urgent' },
  ],
  initiative_statuses: ['active', 'completed', 'dropped'],
  labels: [
    { slug: 'area-api', group_slug: 'area', description: null, open_issue_count: 0 },
    { slug: 'area-cli', group_slug: 'area', description: null, open_issue_count: 1 },
    { slug: 'needs-design', group_slug: null, description: 'Waiting on a design call', open_issue_count: 0 },
  ],
}

const activeInitiative: Initiative = {
  id: 'init-1',
  name: 'Ship the tracker',
  description: null,
  status: 'active',
  status_reason: null,
  priority: 2,
  position: 0,
  created_ts: '2026-10-01T12:00:00Z',
  closed_ts: null,
  issue_count: 0,
  open_count: 0,
  completed_count: 0,
  canceled_count: 0,
  repos: [],
}

const existing: Issue = {
  id: 'id-907',
  number: 907,
  title: 'Route the new paths',
  description: 'The router order',
  acceptance: null,
  repo: 'ichrisbirch',
  type: 'bug',
  status: 'open',
  status_reason: null,
  priority: 1,
  effective_priority: 1,
  rank: 2,
  deferred_until_date: null,
  claimed_by: null,
  claim_expires_ts: null,
  initiative: { id: 'init-9', name: 'Finished migration', status: 'completed', priority: 0 },
  parent: { id: 'id-900', number: 900, title: 'The parent', status: 'open' },
  discovered_from: null,
  duplicate_of: null,
  labels: ['area-cli', 'retired-label'],
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
}

// Mounted closed, then opened: the form loads `editData` on that transition.
async function mountModal(editData: Issue | null = null) {
  const wrapper = mount(AddEditIssueModal, {
    props: { visible: false, editData },
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            issues: { items: [], vocabulary },
            issueInitiatives: { items: [activeInitiative], statusFilter: 'active' },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible', 'focusRef'],
        },
        NeuSelect: true,
        DatePicker: true,
      },
    },
  })
  await wrapper.setProps({ visible: true })
  return wrapper
}

type Wrapper = Awaited<ReturnType<typeof mountModal>>
type Payload = Record<string, unknown>

function created(wrapper: Wrapper): Payload {
  const emitted = wrapper.emitted('create')
  expect(emitted, 'the form emitted no create').toBeTruthy()
  return emitted![0]![0] as Payload
}

function updated(wrapper: Wrapper): Payload {
  const emitted = wrapper.emitted('update')
  expect(emitted, 'the form emitted no update').toBeTruthy()
  return emitted![0]![1] as Payload
}

describe('AddEditIssueModal write contract', () => {
  it('files a task with no priority unless told otherwise, omitting what was left blank', async () => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="issue-title-input"]').setValue('Rank renumber')
    await wrapper.find('form').trigger('submit')
    expect(created(wrapper)).toEqual({ title: 'Rank renumber', type: 'task', priority: 0, status: 'open' })
  })

  it('reads the numbers it waits on as typed, with or without a hash', async () => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="issue-title-input"]').setValue('Route the new paths')
    await wrapper.find('[data-testid="issue-parent-input"]').setValue('#900')
    await wrapper.find('[data-testid="issue-depends-on-input"]').setValue('#906, 905 906')
    await wrapper.find('form').trigger('submit')
    const payload = created(wrapper)
    expect(payload.parent).toBe(900)
    expect(payload.depends_on).toEqual([906, 905])
  })

  it('refuses a dependency that is not a number rather than dropping it', async () => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="issue-title-input"]').setValue('Route the new paths')
    await wrapper.find('[data-testid="issue-depends-on-input"]').setValue('906, router')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('create')).toBeFalsy()
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('not an issue number'), 'error')
  })

  // A group's labels exclude each other, so choosing one sets its sibling down
  // rather than building a pair the API refuses.
  it('keeps one label per group', async () => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="issue-title-input"]').setValue('Rank renumber')
    await wrapper.find('[data-testid="issue-label-area-api"]').trigger('click')
    await wrapper.find('[data-testid="issue-label-needs-design"]').trigger('click')
    await wrapper.find('[data-testid="issue-label-area-cli"]').trigger('click')
    await wrapper.find('form').trigger('submit')
    expect(created(wrapper).labels).toEqual(['needs-design', 'area-cli'])
  })

  it('marks a label the vocabulary does not define, so it can be clicked off', async () => {
    const wrapper = await mountModal(existing)
    const orphan = wrapper.find('[data-testid="issue-label-retired-label"]')
    expect(orphan.classes()).toContain('issue-chips__chip--undefined')
    await orphan.trigger('click')
    await wrapper.find('form').trigger('submit')
    expect(updated(wrapper).labels).toEqual(['area-cli'])
  })

  it('sends a cleared field on an edit as an explicit null', async () => {
    const wrapper = await mountModal(existing)
    await wrapper.find('[data-testid="issue-description-input"]').setValue('')
    await wrapper.find('[data-testid="issue-repo-input"]').setValue('')
    await wrapper.find('[data-testid="issue-parent-input"]').setValue('')
    await wrapper.find('form').trigger('submit')
    const payload = updated(wrapper)
    expect(payload.description).toBeNull()
    expect(payload.repo).toBeNull()
    expect(payload.parent).toBeNull()
    expect(wrapper.emitted('update')![0]![0]).toEqual(existing)
  })

  // A finished initiative takes no new issues, but an issue already in one
  // keeps it as a choice, or saving would silently move it out.
  it('offers a finished initiative only to the issue already in it', async () => {
    const editing = await mountModal(existing)
    const choices = (wrapper: Wrapper) => {
      const select = wrapper
        .findAllComponents({ name: 'NeuSelect' })
        .find((candidate) => candidate.props('dataTestid') === 'issue-initiative-input')
      return (select!.props('options') as { value: string }[]).map((option) => option.value)
    }
    expect(choices(editing)).toEqual(['', 'Ship the tracker', 'Finished migration'])

    const filing = await mountModal()
    expect(choices(filing)).toEqual(['', 'Ship the tracker'])
  })
})
