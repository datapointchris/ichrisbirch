import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ProjectsView from '../ProjectsView.vue'
import { useProjectsStore } from '@/stores/projects'
import type { ProjectWithItemCount, ProjectItemInProject } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

const DraggableStub = {
  template: '<div><slot v-for="item in list" :key="item[itemKey]" name="item" :element="item" /></div>',
  props: ['list', 'itemKey', 'handle', 'ghostClass', 'animation'],
  emits: ['end'],
}

const PROJ_1_ID = 'aaaaaaaa-0000-0000-0000-000000000001'
const PROJ_2_ID = 'aaaaaaaa-0000-0000-0000-000000000002'
const ITEM_1_ID = 'bbbbbbbb-0000-0000-0000-000000000001'
const ITEM_2_ID = 'bbbbbbbb-0000-0000-0000-000000000002'
const ITEM_3_ID = 'bbbbbbbb-0000-0000-0000-000000000003'

const testProjects: ProjectWithItemCount[] = [
  {
    id: PROJ_1_ID,
    name: 'Music Setup',
    description: 'Setting up the studio',
    position: 0,
    created_at: '2026-01-01T00:00:00Z',
    item_count: 3,
  },
  {
    id: PROJ_2_ID,
    name: 'Home Renovation',
    description: undefined,
    position: 1,
    created_at: '2026-02-01T00:00:00Z',
    item_count: 2,
  },
]

const testItems: ProjectItemInProject[] = [
  {
    id: ITEM_1_ID,
    title: 'Decide budget',
    notes: 'Check forums',
    completed: false,
    archived: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    position: 0,
  },
  {
    id: ITEM_2_ID,
    title: 'Research interfaces',
    notes: null,
    completed: true,
    archived: false,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    position: 1,
  },
  {
    id: ITEM_3_ID,
    title: 'Archived item',
    notes: null,
    completed: false,
    archived: true,
    created_at: '2026-01-03T00:00:00Z',
    updated_at: '2026-01-03T00:00:00Z',
    position: 2,
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(ProjectsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            projects: {
              projects: [],
              items: [],
              selectedProjectId: null,
              // selectedProjectIds drives all template conditions — always provide it
              selectedProjectIds: [],
              isViewAll: false,
              loading: false,
              itemsLoading: false,
              error: null,
              itemBlockers: {},
              projectGroups: [],
              itemTasks: {},
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        draggable: DraggableStub,
        Teleport: true,
        AddEditProjectModal: true,
        AddEditProjectItemModal: true,
        ManageDependenciesModal: true,
        ManageProjectsModal: true,
        // ProjectItemTasks renders inline — stub it to avoid fetchItemTasks spy noise
        ProjectItemTasks: true,
      },
    },
  })
}

/** Convenience: state for a single selected project with items visible. */
function selectedState(projectIndex = 0, extraItems: ProjectItemInProject[] = testItems) {
  const project = testProjects[projectIndex]!
  return {
    projects: testProjects,
    selectedProjectId: project.id,
    selectedProjectIds: [project.id],
    items: extraItems,
  }
}

describe('ProjectsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering states ---

  it('shows loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('shows empty state when no projects', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No projects yet')
  })

  it('renders project list from store state', () => {
    const wrapper = createWrapper({ projects: testProjects })
    const items = wrapper.findAll('[data-testid="project-item"]')
    expect(items).toHaveLength(2)
    expect(items[0]!.text()).toContain('Music Setup')
    expect(items[0]!.text()).toContain('3')
    expect(items[1]!.text()).toContain('Home Renovation')
  })

  it('shows "Select a project" when none selected', () => {
    const wrapper = createWrapper({ projects: testProjects })
    expect(wrapper.text()).toContain('Select a project to view items')
  })

  it('shows items pane when project is selected', () => {
    const wrapper = createWrapper(selectedState())
    expect(wrapper.text()).toContain('Music Setup')
    expect(wrapper.find('[data-testid="project-item-add-button"]').exists()).toBe(true)
    const rows = wrapper.findAll('[data-testid="project-item-row"]')
    expect(rows).toHaveLength(3)
    expect(rows[0]!.text()).toContain('Decide budget')
    expect(rows[0]!.text()).toContain('Check forums')
  })

  it('shows empty items message when project has no items', () => {
    const wrapper = createWrapper({ ...selectedState(0, []) })
    expect(wrapper.text()).toContain('No items in this project')
  })

  it('shows items loading state', () => {
    const wrapper = createWrapper({ ...selectedState(), itemsLoading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  // --- CSS classes for item states ---

  it('applies completed class to completed items', () => {
    const wrapper = createWrapper(selectedState())
    const rows = wrapper.findAll('[data-testid="project-item-row"]')
    expect(rows[1]!.classes()).toContain('projects-page__item--completed')
  })

  it('applies archived class to archived items', () => {
    const wrapper = createWrapper(selectedState())
    const rows = wrapper.findAll('[data-testid="project-item-row"]')
    expect(rows[2]!.classes()).toContain('projects-page__item--archived')
  })

  it('applies blocked class and shows blocker text', () => {
    const wrapper = createWrapper({
      ...selectedState(),
      itemBlockers: {
        [ITEM_1_ID]: [{ id: ITEM_2_ID, title: 'Research interfaces', completed: false, archived: false, created_at: '', updated_at: '' }],
      },
    })
    const rows = wrapper.findAll('[data-testid="project-item-row"]')
    expect(rows[0]!.classes()).toContain('projects-page__item--blocked')
    expect(rows[0]!.text()).toContain('Research interfaces')
  })

  it('applies selected class to the active project in sidebar', () => {
    const wrapper = createWrapper({
      projects: testProjects,
      selectedProjectId: PROJ_1_ID,
      selectedProjectIds: [PROJ_1_ID],
    })
    const items = wrapper.findAll('[data-testid="project-item"]')
    expect(items[0]!.classes()).toContain('projects-page__project--selected')
    expect(items[1]!.classes()).not.toContain('projects-page__project--selected')
  })

  // --- Store action wiring ---

  it('calls fetchProjects on mount', () => {
    createWrapper()
    const store = useProjectsStore()
    expect(store.fetchProjects).toHaveBeenCalledOnce()
  })

  it('calls fetchItems when clicking a project row', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()

    await wrapper.findAll('[data-testid="project-item"]')[0]!.trigger('click')

    expect(store.fetchItems).toHaveBeenCalledWith(PROJ_1_ID)
  })

  it('calls toggleProjectSelection when clicking the multi-select checkbox', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()

    // The multi-select button is the second button inside the project row
    const projectRow = wrapper.findAll('[data-testid="project-item"]')[0]!
    const multiBtn = projectRow.find('.projects-page__multi-select-btn')
    await multiBtn.trigger('click')

    expect(store.toggleProjectSelection).toHaveBeenCalledWith(PROJ_1_ID)
  })

  it('calls removeProject when clicking project delete button', async () => {
    // Delete button is in the items header, only visible when a project is selected
    const wrapper = createWrapper(selectedState())
    const store = useProjectsStore()

    await wrapper.find('[data-testid="project-delete-button"]').trigger('click')

    expect(store.removeProject).toHaveBeenCalledWith(PROJ_1_ID)
  })

  it('calls updateItem with completed toggle when clicking complete', async () => {
    const wrapper = createWrapper(selectedState())
    const store = useProjectsStore()

    await wrapper.findAll('[data-testid="project-item-complete-button"]')[0]!.trigger('click')

    expect(store.updateItem).toHaveBeenCalledWith(ITEM_1_ID, { completed: true })
  })

  it('calls archiveItem when clicking archive button', async () => {
    const wrapper = createWrapper(selectedState())
    const store = useProjectsStore()

    await wrapper.findAll('[data-testid="project-item-archive-button"]')[0]!.trigger('click')

    expect(store.archiveItem).toHaveBeenCalledWith(ITEM_1_ID)
  })

  it('calls removeItem when clicking delete item button', async () => {
    const wrapper = createWrapper(selectedState())
    const store = useProjectsStore()

    await wrapper.findAll('[data-testid="project-item-delete-button"]')[0]!.trigger('click')

    expect(store.removeItem).toHaveBeenCalledWith(ITEM_1_ID)
  })

  // --- Modal wiring ---

  it('opens project add modal on add button click', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="project-add-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditProjectModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()
  })

  it('opens project edit modal with project data from items header', async () => {
    // Edit button is in the items header, only visible when a project is selected
    const wrapper = createWrapper(selectedState())

    await wrapper.find('[data-testid="project-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditProjectModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toMatchObject({ id: PROJ_1_ID, name: 'Music Setup' })
  })

  it('opens item add modal on add item button click', async () => {
    const wrapper = createWrapper(selectedState())

    await wrapper.find('[data-testid="project-item-add-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditProjectItemModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()
    expect(modal.props('projectId')).toBe(PROJ_1_ID)
  })

  it('opens item edit modal with item data', async () => {
    const wrapper = createWrapper(selectedState())

    await wrapper.findAll('[data-testid="project-item-edit-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditProjectItemModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual({ id: ITEM_1_ID, title: 'Decide budget', notes: 'Check forums' })
  })

  it('opens dependencies modal with item context', async () => {
    const wrapper = createWrapper(selectedState())

    await wrapper.findAll('[data-testid="project-item-deps-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'ManageDependenciesModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('itemId')).toBe(ITEM_1_ID)
    expect(modal.props('itemTitle')).toBe('Decide budget')
  })

  it('opens projects modal with item context', async () => {
    const wrapper = createWrapper(selectedState())

    await wrapper.findAll('[data-testid="project-item-projects-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'ManageProjectsModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('itemId')).toBe(ITEM_1_ID)
    expect(modal.props('itemTitle')).toBe('Decide budget')
  })

  // --- Search ---

  it('calls searchItems on search submit', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()
    vi.mocked(store.searchItems).mockResolvedValue([
      { id: ITEM_1_ID, title: 'Decide budget', notes: null, completed: false, archived: false, created_at: '', updated_at: '' },
    ])

    await wrapper.find('[data-testid="project-search-input"]').setValue('budget')
    await wrapper.find('form').trigger('submit')
    await vi.dynamicImportSettled()

    expect(store.searchItems).toHaveBeenCalledWith('budget')
  })

  it('renders search results and hides normal items pane', async () => {
    const wrapper = createWrapper(selectedState())
    const store = useProjectsStore()
    vi.mocked(store.searchItems).mockResolvedValue([
      { id: ITEM_1_ID, title: 'Decide budget', notes: null, completed: false, archived: false, created_at: '', updated_at: '' },
    ])

    await wrapper.find('[data-testid="project-search-input"]').setValue('budget')
    await wrapper.find('form').trigger('submit')
    await vi.dynamicImportSettled()

    expect(wrapper.findAll('[data-testid="project-search-result"]')).toHaveLength(1)
    expect(wrapper.text()).toContain('1 result for "budget"')
    expect(wrapper.find('[data-testid="project-item-row"]').exists()).toBe(false)
  })

  it('shows clear button during search and clears on click', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()
    vi.mocked(store.searchItems).mockResolvedValue([])

    expect(wrapper.find('[data-testid="project-search-clear"]').exists()).toBe(false)

    await wrapper.find('[data-testid="project-search-input"]').setValue('test')
    await wrapper.find('form').trigger('submit')
    await vi.dynamicImportSettled()

    expect(wrapper.find('[data-testid="project-search-clear"]').exists()).toBe(true)

    await wrapper.find('[data-testid="project-search-clear"]').trigger('click')

    expect(wrapper.find('[data-testid="project-search-clear"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="project-search-result"]').exists()).toBe(false)
  })

  it('shows no results message for empty search', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()
    vi.mocked(store.searchItems).mockResolvedValue([])

    await wrapper.find('[data-testid="project-search-input"]').setValue('nonexistent')
    await wrapper.find('form').trigger('submit')
    await vi.dynamicImportSettled()

    expect(wrapper.text()).toContain('No results found')
  })

  it('does not search when query is empty', async () => {
    const wrapper = createWrapper({ projects: testProjects })
    const store = useProjectsStore()

    await wrapper.find('form').trigger('submit')

    expect(store.searchItems).not.toHaveBeenCalled()
  })
})
