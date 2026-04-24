import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CookingTechniqueDetailView from '../CookingTechniqueDetailView.vue'
import type { CookingTechnique } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'vinaigrette-ratio' } }),
}))

// Mock the API client so fetchBySlug in the real store hits this instead of the network.
vi.mock('@/api/client', async () => {
  const actual = await vi.importActual<typeof import('@/api/client')>('@/api/client')
  return {
    ...actual,
    api: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    },
  }
})

import { api } from '@/api/client'

function makeTechnique(overrides: Partial<CookingTechnique> = {}): CookingTechnique {
  return {
    id: 1,
    name: 'Vinaigrette Ratio',
    slug: 'vinaigrette-ratio',
    category: 'composition_and_ratio',
    summary: '3:1 oil to acid.',
    body: '## Heading\n\n- bullet one\n- bullet two\n\n**bold text** and a [link](https://example.com).',
    why_it_works: 'Balances taste receptors.',
    common_pitfalls: 'Adding oil too fast breaks the emulsion.',
    source_url: 'https://example.com/video',
    source_name: 'Kevin',
    tags: ['sauce', 'framework'],
    rating: 5,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function createWrapper() {
  return mount(CookingTechniqueDetailView, {
    global: {
      plugins: [
        createTestingPinia({
          // stubActions: false lets the real store actions run, which call our mocked api.get
          stubActions: false,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        AddEditCookingTechniqueModal: true,
      },
    },
  })
}

describe('CookingTechniqueDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders markdown body as HTML when technique loads', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: makeTechnique() })
    const wrapper = createWrapper()
    await flushPromises()

    const body = wrapper.find('[data-testid="cooking-technique-detail-body"]')
    expect(body.exists()).toBe(true)
    expect(body.html()).toContain('<h2>')
    expect(body.html()).toContain('<strong>bold text</strong>')
    expect(body.html()).toContain('<a href="https://example.com">')
  })

  it('renders the summary, category, rating, and tags', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: makeTechnique() })
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('Vinaigrette Ratio')
    expect(wrapper.text()).toContain('3:1 oil to acid.')
    expect(wrapper.text()).toContain('Composition & ratio')
    expect(wrapper.text()).toContain('5/5')
    expect(wrapper.text()).toContain('sauce')
    expect(wrapper.text()).toContain('framework')
  })

  it('renders why_it_works and common_pitfalls when provided', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: makeTechnique() })
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('Why It Works')
    expect(wrapper.text()).toContain('Balances taste receptors')
    expect(wrapper.text()).toContain('Common Pitfalls')
    expect(wrapper.text()).toContain('Adding oil too fast')
  })

  it('hides why_it_works section when value is null', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: makeTechnique({ why_it_works: null, common_pitfalls: null }),
    })
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).not.toContain('Why It Works')
    expect(wrapper.text()).not.toContain('Common Pitfalls')
  })

  it('shows not-found message if fetch fails', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('not found'))
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('Technique not found')
  })
})
