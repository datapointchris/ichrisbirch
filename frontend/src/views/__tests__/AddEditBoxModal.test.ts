import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AddEditBoxModal from '@/components/box-packing/AddEditBoxModal.vue'

const { notify } = vi.hoisted(() => ({ notify: vi.fn() }))
vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: notify, close: vi.fn(), closeAll: vi.fn(), notifications: { value: [] } }),
}))

const editing = { id: 3, name: 'Kitchen', number: 7, size: 'Medium' as const }

async function mountModal(editData: typeof editing | null = null) {
  const wrapper = mount(AddEditBoxModal, {
    props: { visible: false, editData },
    global: {
      plugins: [
        createTestingPinia({
          initialState: { boxPacking: { boxes: [{ ...editing, essential: false, warm: false, liquid: false, items: [] }] } },
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
      },
    },
  })
  await wrapper.setProps({ visible: true })
  return wrapper
}

describe('AddEditBoxModal box number', () => {
  it('refuses to create a box with no number, which the API requires', async () => {
    notify.mockClear()
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="box-name-input"]').setValue('Books')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('create')).toBeUndefined()
    expect(notify).toHaveBeenCalledWith('Box number is required', 'error')
  })

  it('sends the number as a number', async () => {
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="box-name-input"]').setValue('Books')
    await wrapper.find('[data-testid="box-number-input"]').setValue('4')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('create')![0]![0]).toMatchObject({ name: 'Books', number: 4 })
  })

  it('refuses an edit that clears the number', async () => {
    const wrapper = await mountModal(editing)
    await wrapper.find('[data-testid="box-number-input"]').setValue('')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('update')).toBeUndefined()
  })

  it('refuses a number another box already uses', async () => {
    notify.mockClear()
    const wrapper = await mountModal()
    await wrapper.find('[data-testid="box-name-input"]').setValue('Books')
    await wrapper.find('[data-testid="box-number-input"]').setValue('7')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('create')).toBeUndefined()
    expect(notify).toHaveBeenCalledWith('Box number 7 is already used by "Kitchen"', 'error')
  })
})
