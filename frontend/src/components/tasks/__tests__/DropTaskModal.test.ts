import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DropTaskModal from '../DropTaskModal.vue'

function mountModal() {
  return mount(DropTaskModal, {
    props: { visible: true, taskName: 'Oil change' },
    global: {
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible', 'focusRef'],
        },
      },
    },
  })
}

describe('DropTaskModal', () => {
  it('sends the trimmed reason', async () => {
    const wrapper = mountModal()

    await wrapper.find('[data-testid="task-drop-reason-input"]').setValue('  Sold the car  ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('drop')).toEqual([['Sold the car']])
  })

  it('drops with no reason when the box is left blank', async () => {
    const wrapper = mountModal()

    await wrapper.find('[data-testid="task-drop-reason-input"]').setValue('   ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('drop')).toEqual([[undefined]])
  })
})
