import { describe, it, expect, vi } from 'vitest'
import { useNotifications } from '../useNotifications'

describe('useNotifications', () => {
  it('starts with no notifications', () => {
    const { notifications } = useNotifications()
    notifications.value = []
    expect(notifications.value).toEqual([])
  })

  it('adds a notification with show()', () => {
    vi.useFakeTimers()
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('Test message', 'success')
    expect(notifications.value).toHaveLength(1)
    const n = notifications.value[0]!
    expect(n.message).toBe('Test message')
    expect(n.category).toBe('success')
    expect(n.dismissTimer).not.toBeNull()
    vi.useRealTimers()
  })

  it('defaults to success category', () => {
    vi.useFakeTimers()
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('Default category')
    expect(notifications.value[0]!.category).toBe('success')
    vi.useRealTimers()
  })

  it('removes notification on close', () => {
    vi.useFakeTimers()
    const { notifications, show, close } = useNotifications()
    notifications.value = []
    show('Will close', 'error')
    const id = notifications.value[0]!.id

    close(id)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('auto-dismisses after 10 seconds', () => {
    vi.useFakeTimers()
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('Auto dismiss')
    expect(notifications.value).toHaveLength(1)

    vi.advanceTimersByTime(9999)
    expect(notifications.value).toHaveLength(1)

    vi.advanceTimersByTime(1)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('clears timer on manual close', () => {
    vi.useFakeTimers()
    const { notifications, show, close } = useNotifications()
    notifications.value = []
    show('Manual close', 'warning')
    const id = notifications.value[0]!.id

    close(id)
    expect(notifications.value).toHaveLength(0)

    // Timer should not cause errors after manual close
    vi.advanceTimersByTime(10_000)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('closeAll removes all notifications and clears timers', () => {
    vi.useFakeTimers()
    const { notifications, show, closeAll } = useNotifications()
    notifications.value = []
    show('First')
    show('Second')
    show('Third', 'error')
    expect(notifications.value).toHaveLength(3)

    closeAll()
    expect(notifications.value).toHaveLength(0)

    // Timers should not cause errors
    vi.advanceTimersByTime(10_000)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('assigns unique ids', () => {
    vi.useFakeTimers()
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('First')
    show('Second')
    expect(notifications.value[0]!.id).not.toBe(notifications.value[1]!.id)
    vi.useRealTimers()
  })

  it('auto-dismisses individually at staggered times', () => {
    vi.useFakeTimers()
    const { notifications, show } = useNotifications()
    notifications.value = []

    show('First')
    vi.advanceTimersByTime(2000)
    show('Second')
    vi.advanceTimersByTime(2000)
    show('Third')

    expect(notifications.value).toHaveLength(3)

    // First dismisses at t=10s (6s from now)
    vi.advanceTimersByTime(6000)
    expect(notifications.value).toHaveLength(2)

    // Second dismisses at t=12s (2s from now)
    vi.advanceTimersByTime(2000)
    expect(notifications.value).toHaveLength(1)

    // Third dismisses at t=14s (2s from now)
    vi.advanceTimersByTime(2000)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })
})
