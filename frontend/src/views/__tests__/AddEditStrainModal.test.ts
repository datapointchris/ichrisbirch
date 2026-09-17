import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AddEditStrainModal from '@/components/strains/AddEditStrainModal.vue'
import type { Strain, StrainVocabulary } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: vi.fn(), close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const vocabulary: StrainVocabulary = {
  strain_type: [
    { name: 'indica', count: 1 },
    { name: 'sativa_dominant', count: 1 },
  ],
  status: [
    { name: 'tried', count: 1 },
    { name: 'want_to_try', count: 1 },
  ],
  effects: [
    { name: 'creative', count: 1 },
    { name: 'relaxed', count: 1 },
    { name: 'sleepy', count: 0 },
  ],
  flavors: [{ name: 'berry', count: 1 }],
  terpenes: [{ name: 'myrcene', count: 1 }],
}

const existing: Strain = {
  id: 7,
  name: 'Blue Dream',
  breeder: 'Humboldt Seed Company',
  lineage: 'Blueberry x Haze',
  strain_type: 'sativa_dominant',
  status: 'tried',
  thc_percent: 18,
  cbd_percent: 0.1,
  rating: 8,
  effects: ['creative', 'relaxed'],
  flavors: ['berry'],
  terpenes: ['myrcene'],
  tags: ['daytime'],
  source: 'Green Thumb',
  notes: 'Even and predictable.',
  review: 'Consistent batch to batch.',
  last_tried_date: '2026-03-14',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

// Mounted closed, then opened — the page binds `visible` to a ref that starts
// false, and the form loads `editData` on that transition.
async function mountModal(editData: Strain | null = null, vocab: StrainVocabulary = vocabulary) {
  const wrapper = mount(AddEditStrainModal, {
    props: { visible: false, editData },
    global: {
      plugins: [
        createTestingPinia({
          initialState: { strains: { items: [], loading: false, error: null, vocabulary: vocab } },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        // The wrapper renders its default slot with the handlers the form needs.
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

type Payload = Record<string, unknown>
type Wrapper = Awaited<ReturnType<typeof mountModal>>

function createdPayload(wrapper: Wrapper): Payload {
  const emitted = wrapper.emitted('create')
  expect(emitted, 'the form emitted no create').toBeTruthy()
  return emitted![0]![0] as Payload
}

function updatedPayload(wrapper: Wrapper): Payload {
  const emitted = wrapper.emitted('update')
  expect(emitted, 'the form emitted no update').toBeTruthy()
  return emitted![0]![1] as Payload
}

describe('AddEditStrainModal write contract', () => {
  describe('creating', () => {
    it('omits an untouched optional field rather than sending null', async () => {
      const wrapper = await mountModal()
      await wrapper.find('[data-testid="strain-name-input"]').setValue('Runtz')
      await wrapper.find('form').trigger('submit')

      const payload = createdPayload(wrapper)
      expect(payload.name).toBe('Runtz')
      // Absence is what asks for the server default; null would ask for empty.
      for (const key of ['breeder', 'lineage', 'source', 'notes', 'review', 'rating', 'thc_percent']) {
        expect(payload[key], `${key} should be omitted on a create`).toBeUndefined()
      }
    })

    it('sends the fields that were filled in', async () => {
      const wrapper = await mountModal()
      await wrapper.find('[data-testid="strain-name-input"]').setValue('Runtz')
      await wrapper.find('[data-testid="strain-breeder-input"]').setValue('Cookie Fam')
      await wrapper.find('[data-testid="strain-thc-input"]').setValue('22.47')
      await wrapper.find('[data-testid="strain-rating-input"]').setValue('9')
      await wrapper.find('form').trigger('submit')

      const payload = createdPayload(wrapper)
      expect(payload.breeder).toBe('Cookie Fam')
      expect(payload.rating).toBe(9)
      // A two-decimal percentage is a real label value, so the input accepts it.
      expect(payload.thc_percent).toBe(22.47)
    })

    it('starts with no descriptors selected', async () => {
      const wrapper = await mountModal()
      await wrapper.find('[data-testid="strain-name-input"]').setValue('Runtz')
      await wrapper.find('form').trigger('submit')

      expect(createdPayload(wrapper).effects).toEqual([])
    })

    it('refuses to submit with no name', async () => {
      const wrapper = await mountModal()
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('create')).toBeFalsy()
    })
  })

  describe('editing', () => {
    it('loads the strain into the form', async () => {
      const wrapper = await mountModal(existing)
      const name = wrapper.find('[data-testid="strain-name-input"]').element as HTMLInputElement
      expect(name.value).toBe('Blue Dream')
    })

    it('sends null to clear a field, not an empty string', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('[data-testid="strain-breeder-input"]').setValue('')
      await wrapper.find('form').trigger('submit')

      // null is what empties the column. Absence would leave it as it was, and
      // '' would store a blank.
      expect(updatedPayload(wrapper).breeder).toBeNull()
    })

    it('clears a number the same way', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('[data-testid="strain-rating-input"]').setValue('')
      await wrapper.find('form').trigger('submit')

      expect(updatedPayload(wrapper).rating).toBeNull()
    })

    it('sends the shortened list when a chip is deselected', async () => {
      const wrapper = await mountModal(existing)
      expect(existing.effects).toEqual(['creative', 'relaxed'])

      await wrapper.find('[data-testid="strain-effect-creative"]').trigger('click')
      await wrapper.find('form').trigger('submit')

      // The whole list travels on every write, so a deselected chip has to
      // arrive as the shorter list rather than as an absent key.
      expect(updatedPayload(wrapper).effects).toEqual(['relaxed'])
    })

    it('sends the empty list when every chip is deselected', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('[data-testid="strain-effect-creative"]').trigger('click')
      await wrapper.find('[data-testid="strain-effect-relaxed"]').trigger('click')
      await wrapper.find('form').trigger('submit')

      expect(updatedPayload(wrapper).effects).toEqual([])
    })

    it('adds a chip that was not selected', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('[data-testid="strain-effect-sleepy"]').trigger('click')
      await wrapper.find('form').trigger('submit')

      expect(updatedPayload(wrapper).effects).toEqual(['creative', 'relaxed', 'sleepy'])
    })

    it('emits the id being edited', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('update')![0]![0]).toBe(7)
    })

    it('carries the tags through as a list', async () => {
      const wrapper = await mountModal(existing)
      await wrapper.find('[data-testid="strain-tags-input"]').setValue('daytime, evening')
      await wrapper.find('form').trigger('submit')

      expect(updatedPayload(wrapper).tags).toEqual(['daytime', 'evening'])
    })
  })

  describe('a value the vocabulary does not define', () => {
    it('still renders a chip, so the record can be saved', async () => {
      const orphaned = { ...existing, effects: ['relaxed', 'sedative'] }
      const wrapper = await mountModal(orphaned)

      const chip = wrapper.find('[data-testid="strain-effect-sedative"]')
      expect(chip.exists(), 'a value with no chip can be neither kept nor removed').toBe(true)
      expect(chip.classes()).toContain('strain-chips__chip--undefined')
    })

    it('comes off when the chip is clicked', async () => {
      const orphaned = { ...existing, effects: ['relaxed', 'sedative'] }
      const wrapper = await mountModal(orphaned)

      await wrapper.find('[data-testid="strain-effect-sedative"]').trigger('click')
      await wrapper.find('form').trigger('submit')

      expect(updatedPayload(wrapper).effects).toEqual(['relaxed'])
    })
  })

  describe('the vocabulary drives the options', () => {
    it('builds the type dropdown from it', async () => {
      const wrapper = await mountModal()
      const selects = wrapper.findAllComponents({ name: 'NeuSelect' })
      const options = selects[0]!.props('options') as { value: string; label: string }[]
      expect(options.map((o) => o.value)).toEqual(['', 'indica', 'sativa_dominant'])
    })

    it('renders a chip per defined value', async () => {
      const wrapper = await mountModal()
      expect(wrapper.findAll('[data-testid^="strain-effect-"]')).toHaveLength(3)
    })

    it('says so when a vocabulary is empty rather than leaving a blank', async () => {
      const empty: StrainVocabulary = { strain_type: [], status: [], effects: [], flavors: [], terpenes: [] }
      const wrapper = await mountModal(null, empty)
      expect(wrapper.text()).toContain('No effects defined.')
    })
  })
})
