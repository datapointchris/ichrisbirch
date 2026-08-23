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
