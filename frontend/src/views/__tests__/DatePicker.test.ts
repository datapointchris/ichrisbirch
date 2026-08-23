import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import DatePicker from '@/components/DatePicker.vue'

// The calendar is teleported to body, so it is queried through the document
// rather than through the wrapper.
function days(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>('.datepicker__day'))
}

function dayInMonth(label: string): HTMLButtonElement {
  const match = days().find((d) => d.textContent?.trim() === label && !d.classList.contains('datepicker__day--other-month'))
  if (!match) throw new Error(`no day button labelled ${label}`)
  return match
}

const mounted: VueWrapper[] = []

async function openOn(props: Record<string, unknown>): Promise<VueWrapper> {
  const wrapper = mount(DatePicker, { props: { modelValue: '2026-03-14', ...props }, attachTo: document.body })
  mounted.push(wrapper)
  await wrapper.find('.datepicker__toggle').trigger('click')
  await wrapper.vm.$nextTick()
  return wrapper
}

describe('DatePicker max bound', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
  })

  // Unmount rather than clearing body — a live component patching into a wiped
  // teleport target throws, and the throw surfaces in whichever test runs next.
  afterEach(() => {
    while (mounted.length) mounted.pop()!.unmount()
    vi.useRealTimers()
  })

  it('leaves every day selectable when no max is given', async () => {
    await openOn({})
    expect(days().filter((d) => d.disabled)).toHaveLength(0)
  })

  it('disables days after max and emits nothing when one is clicked', async () => {
    const wrapper = await openOn({ max: '2026-03-14' })

    const future = dayInMonth('15')
    expect(future.disabled).toBe(true)

    future.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('keeps max itself selectable', async () => {
    const wrapper = await openOn({ modelValue: '2026-03-10', max: '2026-03-14' })

    const onBound = dayInMonth('14')
    expect(onBound.disabled).toBe(false)

    onBound.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['2026-03-14'])
  })

  it('rejects a typed date past max and restores the accepted value', async () => {
    const wrapper = await openOn({ max: '2026-03-14' })
    const input = wrapper.find('input')

    await input.setValue('2026-04-01')
    await input.trigger('blur')

    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    expect((input.element as HTMLInputElement).value).toBe('Mar 14, 2026')
  })

  it('accepts a typed date within max', async () => {
    const wrapper = await openOn({ max: '2026-03-14' })
    const input = wrapper.find('input')

    await input.setValue('2026-03-12')
    await input.trigger('blur')

    expect(wrapper.emitted('update:modelValue')!.at(-1)).toEqual(['2026-03-12'])
  })

  it('hides the Today shortcut when today is past max', async () => {
    await openOn({ modelValue: '2026-03-01', max: '2026-03-05' })
    expect(document.querySelector('.datepicker__today-btn')).toBeNull()
  })

  it('keeps the Today shortcut when today is within max', async () => {
    await openOn({ max: '2026-03-14' })
    expect(document.querySelector('.datepicker__today-btn')).not.toBeNull()
  })
})

describe('DatePicker typed-date validation', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
  })

  afterEach(() => {
    while (mounted.length) mounted.pop()!.unmount()
    vi.useRealTimers()
  })

  // new Date rolls these over instead of rejecting them, so isNaN alone lets both
  // through and formatDate then re-emits the components that were typed.
  it.each(['2026-03-0', '2026-02-31', '2026-13-01', '2026-00-10'])('refuses %s while it is being typed', async (typed) => {
    const wrapper = await openOn({})
    const input = wrapper.find('input')

    await input.setValue(typed)

    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('emits nothing for the partial days on the way to a full one', async () => {
    const wrapper = await openOn({ modelValue: '2026-03-14', max: '2026-03-14' })
    const input = wrapper.find('input')

    for (const partial of ['2', '20', '202', '2026', '2026-', '2026-0', '2026-03', '2026-03-', '2026-03-0']) {
      await input.setValue(partial)
    }
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()

    await input.setValue('2026-03-09')
    expect(wrapper.emitted('update:modelValue')!.at(-1)).toEqual(['2026-03-09'])
  })

  it('still accepts a real end-of-month day', async () => {
    const wrapper = await openOn({})
    const input = wrapper.find('input')

    await input.setValue('2026-02-28')

    expect(wrapper.emitted('update:modelValue')!.at(-1)).toEqual(['2026-02-28'])
  })
})

describe('DatePicker clearable', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
  })

  afterEach(() => {
    while (mounted.length) mounted.pop()!.unmount()
    vi.useRealTimers()
  })

  it('offers both Clear controls by default', async () => {
    const wrapper = await openOn({})
    expect(wrapper.find('.datepicker__clear').exists()).toBe(true)
    expect(document.querySelector('.datepicker__clear-btn')).not.toBeNull()
  })

  it('hides both Clear controls when clearable is false', async () => {
    const wrapper = await openOn({ clearable: false })
    expect(wrapper.find('.datepicker__clear').exists()).toBe(false)
    expect(document.querySelector('.datepicker__clear-btn')).toBeNull()
  })

  it('does not clear on an emptied field when clearable is false', async () => {
    const wrapper = await openOn({ clearable: false })
    const input = wrapper.find('input')

    await input.setValue('')
    await input.trigger('blur')

    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    expect((input.element as HTMLInputElement).value).toBe('Mar 14, 2026')
  })

  it('still clears on an emptied field by default', async () => {
    const wrapper = await openOn({})
    const input = wrapper.find('input')

    await input.setValue('')
    await input.trigger('blur')

    expect(wrapper.emitted('update:modelValue')!.at(-1)).toEqual([''])
  })
})
