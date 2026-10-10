import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AddEditShoppingItemModal from '@/components/shopping/AddEditShoppingItemModal.vue'
import type { ShoppingItem, ShoppingSection } from '@/api/client'

const costco: ShoppingSection = { id: 'costco-id', name: 'Costco', rank: 1, created_ts: '2026-10-01T00:00:00Z' }
const grocery: ShoppingSection = { id: 'grocery-id', name: 'Grocery', rank: 2, created_ts: '2026-10-01T00:00:00Z' }

const eggs: ShoppingItem = {
  id: 'eggs-id',
  name: 'eggs',
  note: '2 dozen',
  section_id: 'costco-id',
  section_name: 'Costco',
  rank: 1,
  is_needed: true,
  needed_ts: '2026-10-09T00:00:00Z',
  created_ts: '2026-10-01T00:00:00Z',
  purchase_count: 3,
  last_purchased_ts: null,
}

const NeuSelectStub = {
  name: 'NeuSelect',
  props: ['modelValue', 'options'],
  emits: ['update:modelValue'],
  template: '<div data-testid="shopping-item-section-input">{{ modelValue }}</div>',
}

// Mounted closed, then opened, because the form loads on that transition.
async function mountModal(props: { editData?: ShoppingItem | null; initialName?: string } = {}) {
  const wrapper = mount(AddEditShoppingItemModal, {
    props: { visible: false, sections: [grocery, costco], catalog: [eggs], ...props },
    global: {
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible', 'focusRef'],
        },
        NeuSelect: NeuSelectStub,
      },
    },
  })
  await wrapper.setProps({ visible: true })
  return wrapper
}

function select(wrapper: Awaited<ReturnType<typeof mountModal>>) {
  return wrapper.findComponent(NeuSelectStub)
}

describe('AddEditShoppingItemModal', () => {
  it('lists Unsorted, then the sections in rank order', async () => {
    const wrapper = await mountModal()
    expect((select(wrapper).props('options') as { label: string }[]).map((option) => option.label)).toEqual([
      'Unsorted',
      'Costco',
      'Grocery',
    ])
  })

  it('a known name typed in preselects the section it was last in', async () => {
    const wrapper = await mountModal()
    await wrapper.get('[data-testid="shopping-item-name-input"]').setValue('Eggs')
    expect(select(wrapper).props('modelValue')).toBe('costco-id')
  })

  it('choosing Unsorted for a known name sends null, so it leaves its old section', async () => {
    const wrapper = await mountModal({ initialName: 'eggs' })
    select(wrapper).vm.$emit('update:modelValue', 'unsorted')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('create')?.[0]?.[0]).toEqual({ name: 'eggs', note: undefined, section: null })
  })

  it('editing sends the name, the note and the section', async () => {
    const wrapper = await mountModal({ editData: eggs })
    await wrapper.get('[data-testid="shopping-item-note-input"]').setValue('  ')
    select(wrapper).vm.$emit('update:modelValue', 'grocery-id')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('update')?.[0]).toEqual(['eggs-id', { name: 'eggs', note: null, section: 'grocery-id' }])
  })

  it('forgetting an item takes a second tap', async () => {
    const wrapper = await mountModal({ editData: eggs })
    const button = wrapper.get('[data-testid="shopping-item-delete-button"]')

    await button.trigger('click')
    expect(wrapper.emitted('delete')).toBeUndefined()
    await button.trigger('click')
    expect(wrapper.emitted('delete')?.[0]).toEqual(['eggs-id'])
  })

  it('takes an item off the list without forgetting it', async () => {
    const wrapper = await mountModal({ editData: eggs })
    await wrapper.get('[data-testid="shopping-item-remove-button"]').trigger('click')
    expect(wrapper.emitted('remove')?.[0]).toEqual(['eggs-id'])
  })
})
