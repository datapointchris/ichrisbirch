import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
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

const testTasks: Task[] = [
  { id: 1, name: 'Fix broken test', notes: 'Urgent', category: 'Chore', priority: 1, add_date: '2026-03-01T00:00:00Z' },
  { id: 2, name: 'Write docs', category: 'Project', priority: 5, add_date: '2026-03-10T00:00:00Z' },
  { id: 3, name: 'Clean garage', category: 'Chore', priority: 10, add_date: '2026-03-15T00:00:00Z' },
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
            '<div data-testid="task-item"><slot /><button data-testid="task-complete-button" @click="$emit(\'complete\', task.id)">Complete</button><button data-testid="task-extend-button" @click="$emit(\'extend\', task.id, 7)">Extend</button><button data-testid="task-delete-button" @click="$emit(\'delete\', task.id)">Delete</button></div>',
          props: ['task'],
          emits: ['complete', 'extend', 'delete'],
        },
        TaskCompactTodo: true,
        TaskBlockCompleted: true,
        TaskCompactCompleted: true,
        CompletedChart: true,
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

  it('calls extend when child emits extend event', async () => {
    // Need todo page for extend buttons — mock route
    vi.mocked(await import('vue-router')).useRoute = vi.fn().mockReturnValue({
      name: 'tasks-todo',
      fullPath: '/tasks/todo',
      query: {},
    }) as ReturnType<typeof vi.fn>

    const wrapper = createWrapper({ tasks: testTasks })
    const store = useTasksStore()

    await wrapper.find('[data-testid="task-extend-button"]').trigger('click')

    expect(store.extend).toHaveBeenCalledWith(1, 7)
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
