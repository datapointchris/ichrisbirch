import { describe, it, expect, vi } from 'vitest'
import { useNotifications } from '../useNotifications'

describe('useNotifications', () => {
  it('starts with no notifications', () => {
    const { notifications } = useNotifications()
    notifications.value = []
    expect(notifications.value).toEqual([])
  })

  it('adds a notification with show()', () => {
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('Test message', 'success')
    expect(notifications.value).toHaveLength(1)
    const n = notifications.value[0]!
    expect(n.message).toBe('Test message')
    expect(n.category).toBe('success')
    expect(n.closing).toBe(false)
  })

  it('defaults to success category', () => {
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('Default category')
    expect(notifications.value[0]!.category).toBe('success')
  })

  it('marks notification as closing and removes after timeout', () => {
    vi.useFakeTimers()
    const { notifications, show, close } = useNotifications()
    notifications.value = []
    show('Will close', 'error')
    const id = notifications.value[0]!.id

    close(id)
    expect(notifications.value[0]!.closing).toBe(true)
    expect(notifications.value).toHaveLength(1)

    vi.advanceTimersByTime(1000)
    expect(notifications.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('assigns unique ids', () => {
    const { notifications, show } = useNotifications()
    notifications.value = []
    show('First')
    show('Second')
    expect(notifications.value[0]!.id).not.toBe(notifications.value[1]!.id)
  })
})
