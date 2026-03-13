/**
 * Structured API error types for the Vue frontend.
 *
 * Mirrors the error hierarchy in ichrisbirch/api/client/exceptions.py:
 * - ApiHttpError: HTTP 4xx/5xx responses (like APIHTTPError)
 * - ApiNetworkError: Connection/timeout failures (like APIConnectionError)
 *
 * Each error carries structured context (status, detail, request_id) so
 * stores and views never need to manually extract error info from Axios.
 */

// Minimal type for the Axios error shape we need — avoids import resolution
// issues across different TypeScript build modes.
interface AxiosLikeError {
  response?: {
    status: number
    data?: { detail?: string | Record<string, unknown>[] }
    headers?: Record<string, string>
  }
  message?: string
}

export interface ValidationError {
  field: string
  message: string
}

/**
 * Structured API error with full context.
 * Stores and views receive this instead of raw Axios errors.
 */
export class ApiError extends Error {
  /** HTTP status code (undefined for network errors) */
  readonly status?: number
  /** Error detail from API response */
  readonly detail: string
  /** Field-level validation errors from API (422 responses) */
  readonly validationErrors: ValidationError[]
  /** Request ID for cross-service tracing */
  readonly requestId?: string
  /** Whether this is a network/connection error vs HTTP error */
  readonly isNetworkError: boolean

  constructor(opts: {
    message: string
    status?: number
    detail: string
    validationErrors?: ValidationError[]
    requestId?: string
    isNetworkError?: boolean
  }) {
    super(opts.message)
    this.name = 'ApiError'
    this.status = opts.status
    this.detail = opts.detail
    this.validationErrors = opts.validationErrors ?? []
    this.requestId = opts.requestId
    this.isNetworkError = opts.isNetworkError ?? false
  }

  /** Human-readable message suitable for displaying to the user */
  get userMessage(): string {
    if (this.isNetworkError) {
      return 'Unable to reach the server. Check your connection.'
    }
    if (this.status === 422 && this.validationErrors.length > 0) {
      return this.validationErrors.map((e) => `${e.field}: ${e.message}`).join(', ')
    }
    return this.detail
  }
}

/**
 * Extract a structured ApiError from an Axios error.
 * Centralizes all error parsing so it's never duplicated in stores/views.
 */
export function extractApiError(error: unknown): ApiError {
  const axiosError = error as AxiosLikeError

  // Network error (no response received)
  if (!axiosError.response) {
    return new ApiError({
      message: axiosError.message || 'Network error',
      detail: 'Unable to reach the server. Check your connection.',
      isNetworkError: true,
    })
  }

  const { status, data, headers } = axiosError.response
  const requestId = (headers?.['x-request-id'] as string) || undefined

  // Extract detail from various API response formats
  let detail = 'An unexpected error occurred'
  const validationErrors: ValidationError[] = []

  if (data) {
    if (typeof data.detail === 'string') {
      detail = data.detail
    } else if (Array.isArray(data.detail)) {
      // FastAPI validation error format: [{loc: [...], msg: "...", type: "..."}]
      detail = 'Validation error'
      for (const err of data.detail) {
        const loc = (err as Record<string, unknown>).loc as string[] | undefined
        const msg = (err as Record<string, unknown>).msg as string | undefined
        if (loc && msg) {
          const field = loc[loc.length - 1] || 'unknown'
          validationErrors.push({ field, message: msg })
        }
      }
    }
  }

  return new ApiError({
    message: `API ${status}: ${detail}`,
    status,
    detail,
    validationErrors,
    requestId,
  })
}
