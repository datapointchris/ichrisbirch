import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import TasksView from '../TasksView.vue'
import { useTasksStore } from '@/stores/tasks'
import type { Task } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    name: 'tasks',
    fullPath: '/tasks',
    query: {},
  }),
}))

// Stub vuedraggable — its slot-based item rendering needs a shim so tests
// can still reach the inner task components.
vi.mock('vuedraggable', () => ({
  default: {
    name: 'draggable',
    props: ['list', 'itemKey', 'handle'],
    emits: ['end'],
    template:
      '<div><template v-for="(element, index) in list" :key="element[itemKey] ?? index"><slot name="item" :element="element" :index="index" /></template></div>',
  },
}))

const queued = { window_days: 30, pinned: false }
const testTasks: Task[] = [
  {
    ...queued,
    id: 1,
    name: 'Fix broken test',
    notes: 'Urgent',
    category: 'Chore',
    rank_at: '2026-03-31T00:00:00Z',
    add_date: '2026-03-01T00:00:00Z',
  },
  { ...queued, id: 2, name: 'Write docs', category: 'Computer', rank_at: '2026-04-09T00:00:00Z', add_date: '2026-03-10T00:00:00Z' },
  { ...queued, id: 3, name: 'Clean garage', category: 'Chore', rank_at: '2026-04-14T00:00:00Z', add_date: '2026-03-15T00:00:00Z' },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(TasksView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            tasks: {
              tasks: [],
              completedTasks: [],
              loading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        Teleport: true,
        TasksSubnav: true,
        TaskInfoBar: true,
        AddEditTaskModal: true,
        TaskBlockPriority: {
          template:
            '<div data-testid="task-item"><slot /><button data-testid="task-complete-button" @click="$emit(\'complete\', task.id)">Complete</button></div>',
          props: ['task'],
          emits: ['complete'],
        },
        TaskCompactPriority: true,
        TaskBlockTodo: {
          template:
            '<div data-testid="task-item"><slot /><button data-testid="task-complete-button" @click="$emit(\'complete\', task.id)">Complete</button><button data-testid="task-snooze-button" @click="$emit(\'snooze\', task.id)">Snooze</button><button data-testid="task-drop-button" @click="$emit(\'drop\', task.id)">Drop</button><button data-testid="task-pin-button" @click="$emit(\'pin\', task.id, !task.pinned)">Pin</button><button data-testid="task-delete-button" @click="$emit(\'delete\', task.id)">Delete</button></div>',
          props: ['task'],
          emits: ['complete', 'snooze', 'drop', 'pin', 'delete'],
        },
        TaskCompactTodo: true,
        TaskBlockCompleted: true,
        TaskCompactCompleted: true,
        TaskBlockDropped: {
          template:
            '<div data-testid="task-dropped-item"><button data-testid="task-reopen-button" @click="$emit(\'reopen\', task.id)">Reopen</button></div>',
          props: ['task'],
          emits: ['reopen', 'delete'],
        },
        TaskCompactDropped: true,
        DropTaskModal: true,
        CompletedChart: true,
        NeuToggleGroup: true,
      },
    },
  })
}

describe('TasksView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('renders priority page with top 5 tasks', () => {
    const wrapper = createWrapper({ tasks: testTasks })
    expect(wrapper.text()).toContain('Priority Tasks')
    expect(wrapper.text()).toContain('Completed Today')
  })

  // --- Store action wiring ---

  it('calls fetchTodo on mount', () => {
    createWrapper()
    const store = useTasksStore()
    expect(store.fetchTodo).toHaveBeenCalledOnce()
  })

  it('calls complete when child emits complete event', async () => {
    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()
    vi.mocked(store.complete).mockResolvedValue({
      ...testTasks[0]!,
      complete_date: '2026-03-29T00:00:00Z',
    })

    await wrapper.find('[data-testid="task-complete-button"]').trigger('click')

    expect(store.complete).toHaveBeenCalledWith(1)
  })

  it.each([
    ['task-snooze-button', 'snooze', [1]],
    ['task-pin-button', 'setPinned', [1, true]],
  ] as const)('%s calls store.%s', async (testId, action, args) => {
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-todo',
      fullPath: '/tasks/todo',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()

    await wrapper.find(`[data-testid="${testId}"]`).trigger('click')

    expect(store[action]).toHaveBeenCalledWith(...args)
  })

  it('Drop asks for a reason first and sends the one given', async () => {
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-todo',
      fullPath: '/tasks/todo',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()
    const modal = wrapper.findComponent({ name: 'DropTaskModal' })
    expect(modal.props('visible')).toBe(false)

    await wrapper.find('[data-testid="task-drop-button"]').trigger('click')

    expect(store.drop).not.toHaveBeenCalled()
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('taskName')).toBe('Fix broken test')

    modal.vm.$emit('drop', 'Moved away')
    await wrapper.vm.$nextTick()

    expect(store.drop).toHaveBeenCalledWith(1, 'Moved away')
  })

  it('the Dropped toggle on the completed page loads dropped tasks, and Reopen reopens one', async () => {
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-completed',
      fullPath: '/tasks/completed',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const dropped = { ...testTasks[1]!, drop_date: '2026-03-20T00:00:00Z', drop_reason: 'meh' }
    const wrapper = createWrapper({ droppedTasks: [dropped] })
    const store = useTasksStore()
    await flushPromises()
    expect(store.fetchCompleted).toHaveBeenCalledOnce()
    expect(wrapper.find('[data-testid="task-dropped-item"]').exists()).toBe(false)

    const toggle = wrapper.findAllComponents({ name: 'NeuToggleGroup' }).find((c) => c.props('dataTestid') === 'tasks-closed-view')!
    toggle.vm.$emit('update:modelValue', 'dropped')
    await wrapper.vm.$nextTick()

    expect(store.fetchDropped).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Dropped Tasks')

    await wrapper.find('[data-testid="task-reopen-button"]').trigger('click')

    expect(store.reopen).toHaveBeenCalledWith(2)
  })

  it('a drag sends the dropped task a rank_at between its new neighbors', async () => {
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-todo',
      fullPath: '/tasks/todo',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()
    const draggable = wrapper.findComponent({ name: 'draggable' })
    // vuedraggable mutates the list before emitting end: task 3 now sits first.
    const list = draggable.props('list') as Task[]
    list.unshift(list.pop()!)

    draggable.vm.$emit('end', { oldIndex: 2, newIndex: 0 })
    await wrapper.vm.$nextTick()

    expect(store.move).toHaveBeenCalledWith(3, '2026-03-30T00:00:00.000Z', undefined)
  })

  it('calls remove when child emits delete event', async () => {
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-todo',
      fullPath: '/tasks/todo',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()

    await wrapper.find('[data-testid="task-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  // --- Modal wiring ---

  it('passes showAddTask to modal component', () => {
    const wrapper = createWrapper()
    const modal = wrapper.findComponent({ name: 'AddEditTaskModal' })
    expect(modal.props('visible')).toBe(false)
  })
})
