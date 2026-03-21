import { reactive, nextTick } from 'vue'
import { useNotifications } from '@/composables/useNotifications'

/**
 * Composable for managing form field validation errors with animated feedback.
 *
 * Handles error state, CSS animation re-triggering (via nextTick toggle),
 * and optional notification display. Works with the `textbox--error` CSS class.
 *
 * Usage:
 *   const { errors, validate, clearError, clearAll } = useFieldErrors()
 *
 *   // Template:  :class="{ 'textbox--error': errors.fieldName }"
 *   //            @input="clearError('fieldName')"
 *
 *   // Validation: validate({ fieldName: myValidator(form.fieldName) })
 *   //             Returns true if all fields pass, false if any fail
 */
export function useFieldErrors() {
  const errors = reactive<Record<string, boolean>>({})
  const { show: notify } = useNotifications()

  /**
   * Validate multiple fields at once. Each key is a field name, each value
   * is either an error message string (fail) or null (pass).
   * Failed fields get their error state set (with animation re-trigger),
   * and error messages are shown as notifications.
   * Returns true if all fields pass.
   */
  function validate(fields: Record<string, string | null>): boolean {
    let allValid = true
    for (const [field, message] of Object.entries(fields)) {
      if (message) {
        errors[field] = false
        nextTick(() => {
          errors[field] = true
        })
        notify(message, 'error')
        allValid = false
      } else {
        errors[field] = false
      }
    }
    return allValid
  }

  function setError(field: string, message?: string) {
    errors[field] = false
    nextTick(() => {
      errors[field] = true
    })
    if (message) {
      notify(message, 'error')
    }
  }

  function clearError(field: string) {
    errors[field] = false
  }

  function clearAll() {
    for (const key of Object.keys(errors)) {
      errors[key] = false
    }
  }

  function hasError(field: string): boolean {
    return errors[field] ?? false
  }

  return { errors, validate, setError, clearError, clearAll, hasError }
}
