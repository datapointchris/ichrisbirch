import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ArticlesView from '../ArticlesView.vue'
import { useArticlesStore } from '@/stores/articles'
import type { Article } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => date.slice(0, 10),
}))

const testArticles: Article[] = [
  {
    id: 1,
    title: 'Understanding OKLCH Colors',
    url: 'https://example.com/oklch',
    tags: ['css', 'color'],
    summary: 'A deep dive into OKLCH color space',
    save_date: '2026-03-01T00:00:00Z',
    read_count: 2,
    is_favorite: true,
    is_current: false,
    is_archived: false,
  },
  {
    id: 2,
    title: 'Docker Compose Best Practices',
    url: 'https://example.com/docker',
    tags: ['docker', 'devops'],
    summary: 'Production patterns for compose',
    notes: 'Relevant to ichrisbirch infra',
    save_date: '2026-03-15T00:00:00Z',
    read_count: 0,
    is_favorite: false,
    is_current: true,
    is_archived: false,
  },
  {
    id: 3,
    title: 'Archived Article',
    url: 'https://example.com/archived',
    tags: ['old'],
    summary: 'No longer needed',
    save_date: '2026-01-01T00:00:00Z',
    read_count: 5,
    is_favorite: false,
    is_current: false,
    is_archived: true,
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(ArticlesView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            articles: {
              articles: [],
              currentArticle: null,
              loading: false,
              error: null,
              summarizing: false,
              showArchived: false,
              searchQuery: '',
              searchResults: [],
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        Teleport: true,
        ArticlesSubnav: true,
        AddEditArticleModal: true,
      },
    },
  })
}

describe('ArticlesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering states ---

  it('shows loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('shows empty state when no articles', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No articles yet.')
  })

  it('renders article list from store state', () => {
    const wrapper = createWrapper({ articles: testArticles })
    const items = wrapper.findAll('[data-testid="article-item"]')
    expect(items).toHaveLength(3)
    expect(items[0]!.text()).toContain('Docker Compose Best Practices')
    expect(items[0]!.text()).toContain('docker, devops')
  })

  it('applies favorite class to favorited articles', () => {
    const wrapper = createWrapper({ articles: testArticles })
    const items = wrapper.findAll('[data-testid="article-item"]')
    // Articles are sorted by save_date desc, so index 1 is the OKLCH article (favorite)
    const favoriteItem = items.find((item) => item.text().includes('OKLCH'))!
    expect(favoriteItem.classes()).toContain('articles__row--favorite')
  })

  it('applies current class to current article', () => {
    const wrapper = createWrapper({ articles: testArticles })
    const items = wrapper.findAll('[data-testid="article-item"]')
    const currentItem = items.find((item) => item.text().includes('Docker Compose'))!
    expect(currentItem.classes()).toContain('articles__row--current')
  })

  it('shows active star icon for favorited articles', () => {
    const wrapper = createWrapper({ articles: testArticles })
    const favButtons = wrapper.findAll('[data-testid="article-favorite-button"]')
    const oklchFav = favButtons.find((btn) => btn.element.closest('[data-testid="article-item"]')?.textContent?.includes('OKLCH'))
    expect(oklchFav!.classes()).toContain('articles__star--active')
  })

  // --- Current article banner ---

  it('shows current article banner when one is set', () => {
    const wrapper = createWrapper({
      articles: testArticles,
      currentArticle: testArticles[1],
    })
    expect(wrapper.text()).toContain('Current Article')
    expect(wrapper.text()).toContain('Docker Compose Best Practices')
  })

  it('hides current article banner during search', () => {
    const wrapper = createWrapper({
      articles: testArticles,
      currentArticle: testArticles[1],
      searchQuery: 'docker',
      searchResults: [testArticles[1]],
    })
    expect(wrapper.find('.articles__current').exists()).toBe(false)
  })

  // --- Expand detail ---

  it('expands article detail on chevron click', async () => {
    const wrapper = createWrapper({ articles: testArticles })

    const firstExpand = wrapper.findAll('[data-testid="article-expand-button"]')[0]!
    await firstExpand.trigger('click')

    const detail = wrapper.find('.articles__detail--open')
    expect(detail.exists()).toBe(true)
    expect(detail.text()).toContain('Production patterns for compose')
  })

  it('shows notes in expanded detail when present', async () => {
    const wrapper = createWrapper({ articles: testArticles })

    // Expand Docker article (first in sorted order — newest first)
    await wrapper.findAll('[data-testid="article-expand-button"]')[0]!.trigger('click')

    const detail = wrapper.find('.articles__detail--open')
    expect(detail.text()).toContain('Relevant to ichrisbirch infra')
  })

  it('collapses detail on second click', async () => {
    const wrapper = createWrapper({ articles: testArticles })

    const expandBtn = wrapper.findAll('[data-testid="article-expand-button"]')[0]!
    await expandBtn.trigger('click')
    expect(wrapper.find('.articles__detail--open').exists()).toBe(true)

    await expandBtn.trigger('click')
    expect(wrapper.find('.articles__detail--open').exists()).toBe(false)
  })

  // --- Store action wiring ---

  it('calls fetchAll and fetchCurrent on mount', () => {
    createWrapper()
    const store = useArticlesStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
    expect(store.fetchCurrent).toHaveBeenCalledOnce()
  })

  it('calls toggleFavorite when clicking star icon', async () => {
    const wrapper = createWrapper({ articles: testArticles })
    const store = useArticlesStore()

    await wrapper.findAll('[data-testid="article-favorite-button"]')[0]!.trigger('click')

    // First displayed article (sorted by save_date desc) is Docker (id: 2)
    expect(store.toggleFavorite).toHaveBeenCalledWith(2)
  })

  it('calls remove when clicking delete button', async () => {
    const wrapper = createWrapper({ articles: testArticles })
    const store = useArticlesStore()

    await wrapper.findAll('[data-testid="article-delete-button"]')[0]!.trigger('click')

    expect(store.remove).toHaveBeenCalledWith(2)
  })

  it('calls markRead from current article banner', async () => {
    const wrapper = createWrapper({
      articles: testArticles,
      currentArticle: testArticles[1],
    })
    const store = useArticlesStore()

    const markReadBtn = wrapper.findAll('.articles__current-actions button').find((b) => b.text() === 'Mark Read')!
    await markReadBtn.trigger('click')

    expect(store.markRead).toHaveBeenCalledWith(2)
  })

  it('calls removeCurrent from current article banner', async () => {
    const wrapper = createWrapper({
      articles: testArticles,
      currentArticle: testArticles[1],
    })
    const store = useArticlesStore()

    const removeBtn = wrapper.findAll('.articles__current-actions button').find((b) => b.text() === 'Remove Current')!
    await removeBtn.trigger('click')

    expect(store.removeCurrent).toHaveBeenCalledWith(2)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="article-add-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditArticleModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()
  })

  it('opens edit modal with article data', async () => {
    const wrapper = createWrapper({ articles: testArticles })

    await wrapper.findAll('[data-testid="article-edit-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditArticleModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual({
      id: 2,
      title: 'Docker Compose Best Practices',
      url: 'https://example.com/docker',
      tags: ['docker', 'devops'],
      summary: 'Production patterns for compose',
      notes: 'Relevant to ichrisbirch infra',
    })
  })

  // --- Search ---

  it('calls search on form submit', async () => {
    const wrapper = createWrapper({ articles: testArticles })
    const store = useArticlesStore()

    await wrapper.find('input[type="text"]').setValue('docker')
    await wrapper.find('form').trigger('submit')

    expect(store.search).toHaveBeenCalledWith('docker')
  })

  it('does not search when query is empty', async () => {
    const wrapper = createWrapper({ articles: testArticles })
    const store = useArticlesStore()

    await wrapper.find('form').trigger('submit')

    expect(store.search).not.toHaveBeenCalled()
  })

  it('shows search active label and clear button', () => {
    const wrapper = createWrapper({
      articles: testArticles,
      searchQuery: 'docker',
      searchResults: [testArticles[1]],
    })

    expect(wrapper.text()).toContain('Showing results for: docker')
    expect(wrapper.find('.button--danger').exists()).toBe(true)
  })

  it('shows empty search message when no results', () => {
    const wrapper = createWrapper({
      searchQuery: 'nonexistent',
      searchResults: [],
    })

    expect(wrapper.text()).toContain('No articles match your search.')
  })

  it('calls clearSearch when clicking clear button', async () => {
    const wrapper = createWrapper({
      articles: testArticles,
      searchQuery: 'docker',
      searchResults: [testArticles[1]],
    })
    const store = useArticlesStore()

    await wrapper.find('.button--danger').trigger('click')

    expect(store.clearSearch).toHaveBeenCalled()
  })

  // --- Archive toggle ---

  it('renders archive toggle button', () => {
    const wrapper = createWrapper({ articles: testArticles })
    const toggle = wrapper.find('[data-testid="article-archive-toggle"]')
    expect(toggle.exists()).toBe(true)
    expect(toggle.text()).toContain('Show Archived')
  })

  it('calls setShowArchived when clicking archive toggle', async () => {
    const wrapper = createWrapper({ articles: testArticles })
    const store = useArticlesStore()

    await wrapper.find('[data-testid="article-archive-toggle"]').trigger('click')

    expect(store.setShowArchived).toHaveBeenCalledWith(true)
  })

  it('shows "Show Active" label when viewing archived', () => {
    const wrapper = createWrapper({ articles: testArticles, showArchived: true })
    const toggle = wrapper.find('[data-testid="article-archive-toggle"]')
    expect(toggle.text()).toContain('Show Active')
  })
})
