import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import BooksView from '../BooksView.vue'
import { useBooksStore } from '@/stores/books'
import type { Book } from '@/api/client'

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

const testBooks: Book[] = [
  {
    id: 1,
    title: 'Dune',
    author: 'Frank Herbert',
    tags: ['sci-fi', 'classic'],
    progress: 'read',
    ownership: 'owned',
    rating: 5,
    priority: 1,
  },
  {
    id: 2,
    title: 'Neuromancer',
    author: 'William Gibson',
    tags: ['cyberpunk'],
    progress: 'reading',
    ownership: 'owned',
    rating: 4,
    priority: 2,
  },
  {
    id: 3,
    title: 'Snow Crash',
    author: 'Neal Stephenson',
    tags: ['sci-fi'],
    progress: 'unread',
    ownership: 'to_purchase',
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(BooksView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            books: {
              books: [],
              loading: false,
              error: null,
              sortField: 'title',
              sortDirection: 'asc',
              activeFilter: 'all',
              ownershipFilter: 'all',
              searchQuery: '',
              isSearchActive: false,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AddEditBookModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('BooksView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useBooksStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no books match filter', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No books match the selected filter.')
  })

  it('renders book rows with title, author, and progress', () => {
    const wrapper = createWrapper({ books: testBooks })
    const rows = wrapper.findAll('[data-testid="book-item"]')
    expect(rows.length).toBe(3)
    expect(rows[0]!.text()).toContain('Dune')
    expect(rows[0]!.text()).toContain('Frank Herbert')
    expect(rows[0]!.text()).toContain('Read')
  })

  it('applies progress CSS class to book rows', () => {
    const wrapper = createWrapper({ books: testBooks })
    const rows = wrapper.findAll('[data-testid="book-item"]')
    expect(rows[0]!.classes()).toContain('book--read')
    expect(rows[1]!.classes()).toContain('book--reading')
    expect(rows[2]!.classes()).toContain('book--unread')
  })

  it('renders status counters in info bar', () => {
    const wrapper = createWrapper({ books: testBooks })
    expect(wrapper.text()).toContain('Read: 1')
    expect(wrapper.text()).toContain('Reading: 1')
    expect(wrapper.text()).toContain('Unread: 1')
    expect(wrapper.text()).toContain('Total: 3')
  })

  // --- Detail expand ---

  it('expands book detail on chevron click', async () => {
    const wrapper = createWrapper({ books: testBooks })
    const chevron = wrapper.find('.books__chevron')
    await chevron.trigger('click')

    const detail = wrapper.find('.books__detail--open')
    expect(detail.exists()).toBe(true)
    expect(detail.text()).toContain('sci-fi, classic')
  })

  // --- Store action wiring ---

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ books: testBooks })
    const store = useBooksStore()

    await wrapper.find('[data-testid="book-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  it('calls setFilter when status counter clicked', async () => {
    const wrapper = createWrapper({ books: testBooks })
    const store = useBooksStore()

    await wrapper.find('.book--read.book-filter').trigger('click')

    expect(store.setFilter).toHaveBeenCalledWith('read')
  })

  it('calls setSort when column header clicked', async () => {
    const wrapper = createWrapper({ books: testBooks })
    const store = useBooksStore()

    await wrapper.find('.books__sortable').trigger('click')

    expect(store.setSort).toHaveBeenCalledWith('title')
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditBookModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="book-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditBookModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditBookModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with book data on edit button click', async () => {
    const wrapper = createWrapper({ books: testBooks })

    await wrapper.find('[data-testid="book-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditBookModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testBooks[0])
  })

  // --- Search ---

  it('calls search when form submitted with input', async () => {
    const wrapper = createWrapper({ books: testBooks })
    const store = useBooksStore()

    const input = wrapper.find('.textbox')
    await input.setValue('dune')

    await wrapper.find('.books__search').trigger('submit')

    expect(store.search).toHaveBeenCalledWith('dune')
  })

  it('calls clearSearch when clear button clicked', async () => {
    const wrapper = createWrapper({ books: testBooks, isSearchActive: true, searchQuery: 'dune' })
    const store = useBooksStore()

    await wrapper.find('.button--danger').trigger('click')

    expect(store.clearSearch).toHaveBeenCalledOnce()
  })
})
