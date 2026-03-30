import { describe, it, expect } from 'vitest'
import { ApiError, extractApiError } from '../errors'

describe('ApiError', () => {
  it('carries structured context', () => {
    const err = new ApiError({
      message: 'API 422: Validation error',
      status: 422,
      detail: 'Validation error',
      validationErrors: [{ field: 'name', message: 'Required' }],
      requestId: 'abc123',
    })

    expect(err.status).toBe(422)
    expect(err.detail).toBe('Validation error')
    expect(err.validationErrors).toHaveLength(1)
    expect(err.requestId).toBe('abc123')
    expect(err.isNetworkError).toBe(false)
  })

  it('provides user-friendly message for network errors', () => {
    const err = new ApiError({
      message: 'Network error',
      detail: 'Unable to reach the server. Check your connection.',
      isNetworkError: true,
    })

    expect(err.userMessage).toBe('Unable to reach the server. Check your connection.')
  })

  it('provides user-friendly message for validation errors', () => {
    const err = new ApiError({
      message: 'API 422',
      status: 422,
      detail: 'Validation error',
      validationErrors: [
        { field: 'name', message: 'Required' },
        { field: 'due_date', message: 'Must be in the future' },
      ],
    })

    expect(err.userMessage).toBe('name: Required, due_date: Must be in the future')
  })

  it('falls back to detail for non-validation errors', () => {
    const err = new ApiError({
      message: 'API 403',
      status: 403,
      detail: 'Permission denied',
    })

    expect(err.userMessage).toBe('Permission denied')
  })
})

describe('extractApiError', () => {
  it('extracts error from HTTP response with string detail', () => {
    const axiosError = {
      response: {
        status: 404,
        data: { detail: 'Countdown not found' },
        headers: { 'x-request-id': 'req-123' },
      },
      message: 'Request failed with status code 404',
    }

    const err = extractApiError(axiosError)

    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(404)
    expect(err.detail).toBe('Countdown not found')
    expect(err.requestId).toBe('req-123')
    expect(err.isNetworkError).toBe(false)
  })

  it('extracts validation errors from FastAPI 422 response', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'name'], msg: 'Field required', type: 'missing' },
            { loc: ['body', 'due_date'], msg: 'Invalid date format', type: 'value_error' },
          ],
        },
        headers: {},
      },
      message: 'Request failed',
    }

    const err = extractApiError(axiosError)

    expect(err.status).toBe(422)
    expect(err.validationErrors).toEqual([
      { field: 'name', message: 'Field required' },
      { field: 'due_date', message: 'Invalid date format' },
    ])
    expect(err.userMessage).toBe('name: Field required, due_date: Invalid date format')
  })

  it('handles network errors (no response)', () => {
    const axiosError = {
      message: 'Network Error',
      response: undefined,
    }

    const err = extractApiError(axiosError)

    expect(err.isNetworkError).toBe(true)
    expect(err.status).toBeUndefined()
    expect(err.userMessage).toBe('Unable to reach the server. Check your connection.')
  })

  it('handles empty/missing detail in response', () => {
    const axiosError = {
      response: {
        status: 500,
        data: {},
        headers: {},
      },
      message: 'Internal Server Error',
    }

    const err = extractApiError(axiosError)

    expect(err.status).toBe(500)
    expect(err.detail).toBe('An unexpected error occurred')
  })

  it('handles null data in response', () => {
    const axiosError = {
      response: {
        status: 502,
        data: null as unknown as undefined,
        headers: {},
      },
      message: 'Bad Gateway',
    }

    const err = extractApiError(axiosError)

    expect(err.status).toBe(502)
    expect(err.detail).toBe('An unexpected error occurred')
  })

  it('falls back to "Network error" when message is missing', () => {
    const axiosError = { response: undefined }

    const err = extractApiError(axiosError)

    expect(err.isNetworkError).toBe(true)
    expect(err.message).toBe('Network error')
  })

  it('skips validation entries missing loc or msg', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'name'], msg: 'Required', type: 'missing' },
            { msg: 'No loc field', type: 'missing' },
            { loc: ['body', 'age'], type: 'missing' },
          ],
        },
        headers: {},
      },
      message: 'Request failed',
    }

    const err = extractApiError(axiosError)

    expect(err.validationErrors).toEqual([{ field: 'name', message: 'Required' }])
  })

  it('handles missing x-request-id header', () => {
    const axiosError = {
      response: {
        status: 403,
        data: { detail: 'Forbidden' },
        headers: {},
      },
      message: 'Forbidden',
    }

    const err = extractApiError(axiosError)

    expect(err.requestId).toBeUndefined()
  })
})
