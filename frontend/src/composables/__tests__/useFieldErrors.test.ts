import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { useFieldErrors } from '../useFieldErrors'

// Mock useNotifications so we can verify notification calls
const mockShow = vi.fn()
vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: mockShow }),
}))

describe('useFieldErrors', () => {
  beforeEach(() => {
    mockShow.mockClear()
  })

  it('starts with no errors', () => {
    const { errors, hasError } = useFieldErrors()
    expect(hasError('name')).toBe(false)
    expect(errors.name).toBeUndefined()
  })

  it('setError sets the error state and shows notification', async () => {
    const { errors, setError, hasError } = useFieldErrors()
    setError('name', 'Name is required')
    await nextTick()
    expect(hasError('name')).toBe(true)
    expect(errors.name).toBe(true)
    expect(mockShow).toHaveBeenCalledWith('Name is required', 'error')
  })

  it('setError without message does not notify', async () => {
    const { setError, hasError } = useFieldErrors()
    setError('name')
    await nextTick()
    expect(hasError('name')).toBe(true)
    expect(mockShow).not.toHaveBeenCalled()
  })

  it('clearError removes the error state', async () => {
    const { setError, clearError, hasError } = useFieldErrors()
    setError('name')
    await nextTick()
    expect(hasError('name')).toBe(true)
    clearError('name')
    expect(hasError('name')).toBe(false)
  })

  it('clearAll removes all errors', async () => {
    const { setError, clearAll, hasError } = useFieldErrors()
    setError('name')
    setError('email')
    await nextTick()
    expect(hasError('name')).toBe(true)
    expect(hasError('email')).toBe(true)
    clearAll()
    expect(hasError('name')).toBe(false)
    expect(hasError('email')).toBe(false)
  })

  it('validate returns true when all fields pass', () => {
    const { validate } = useFieldErrors()
    const result = validate({ name: null, email: null })
    expect(result).toBe(true)
    expect(mockShow).not.toHaveBeenCalled()
  })

  it('validate returns false and sets errors when fields fail', async () => {
    const { validate, hasError } = useFieldErrors()
    const result = validate({
      name: null,
      email: 'Invalid email',
      number: 'Must be positive',
    })
    await nextTick()
    expect(result).toBe(false)
    expect(hasError('name')).toBe(false)
    expect(hasError('email')).toBe(true)
    expect(hasError('number')).toBe(true)
    expect(mockShow).toHaveBeenCalledTimes(2)
    expect(mockShow).toHaveBeenCalledWith('Invalid email', 'error')
    expect(mockShow).toHaveBeenCalledWith('Must be positive', 'error')
  })

  it('validate clears previously set errors on passing fields', async () => {
    const { validate, setError, hasError } = useFieldErrors()
    setError('name')
    await nextTick()
    expect(hasError('name')).toBe(true)
    validate({ name: null })
    expect(hasError('name')).toBe(false)
  })

  it('setError re-triggers animation via nextTick toggle', async () => {
    const { errors, setError } = useFieldErrors()
    setError('name')
    await nextTick()
    expect(errors.name).toBe(true)
    // Call again — should toggle off then back on
    setError('name')
    expect(errors.name).toBe(false) // toggled off synchronously
    await nextTick()
    expect(errors.name).toBe(true) // toggled back on after tick
  })
})
