<template>
  <div>
    <ArticlesSubnav />

    <div class="grid grid--one-column-wide">
      <div class="add-item-wrapper">
        <h2>Bulk Add New Articles</h2>

        <!-- Submit Form -->
        <form
          v-if="!batchId"
          class="add-item-form"
          @submit.prevent="handleSubmit"
        >
          <div class="add-item-form__item add-item-form__item--full-width">
            <label for="text">URLs for Articles (one per line)</label>
            <textarea
              id="text"
              v-model="urlText"
              rows="12"
              class="textbox"
              placeholder="https://example.com/article1&#10;https://example.com/article2&#10;..."
            ></textarea>
          </div>
          <div class="add-item-form__item--full-width">
            <button
              type="submit"
              class="button"
              :disabled="submitting"
            >
              <span class="button__text">{{ submitting ? 'Submitting...' : 'Add New Articles' }}</span>
            </button>
          </div>
        </form>

        <!-- Progress Display -->
        <div
          v-else
          class="add-item-form"
        >
          <div class="add-item-form__item add-item-form__item--full-width">
            <p class="bulk-import__status">{{ statusText }}</p>
            <p>
              Processed: <strong>{{ batch?.processed ?? 0 }}</strong> /
              <strong>{{ batch?.total ?? 0 }}</strong>
            </p>
            <p>
              Succeeded: <strong>{{ batch?.succeeded ?? 0 }}</strong> | Failed:
              <strong>{{ batch?.failed_count ?? 0 }}</strong>
            </p>
          </div>

          <div
            v-if="batch && batch.results.length > 0"
            class="add-item-form__item add-item-form__item--full-width"
          >
            <h3>Succeeded</h3>
            <textarea
              rows="8"
              class="textbox"
              disabled
              :value="batch.results.map((r) => r.url).join('\n')"
            ></textarea>
          </div>

          <div
            v-if="batch && batch.errors.length > 0"
            class="add-item-form__item add-item-form__item--full-width"
          >
            <h3>Failed</h3>
            <textarea
              rows="8"
              class="textbox"
              disabled
              :value="batch.errors.map((e) => `${e.url}\n  ${e.error}`).join('\n\n')"
            ></textarea>
          </div>

          <div class="add-item-form__item">
            <button
              type="button"
              class="button"
              @click="resetForm"
            >
              <span class="button__text">Bulk Add More Articles</span>
            </button>
          </div>
          <div class="add-item-form__item">
            <RouterLink
              to="/articles"
              class="button"
            >
              <span class="button__text">All Articles</span>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { useNotifications } from '@/composables/useNotifications'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'
import { createLogger } from '@/utils/logger'
import type { BulkImportResponse, BulkImportStatus } from '@/api/client'

const logger = createLogger('ArticleBulkImport')
const { show: notify } = useNotifications()

const urlText = ref('')
const submitting = ref(false)
const batchId = ref('')
const batch = ref<BulkImportStatus | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const statusText = computed(() => {
  if (!batch.value) return 'Queued... waiting for processing to begin.'
  switch (batch.value.status) {
    case 'completed':
      return 'Import complete.'
    case 'processing':
      return 'Processing...'
    default:
      return 'Queued... waiting for processing to begin.'
  }
})

async function handleSubmit() {
  const urls = urlText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
  if (urls.length === 0) return

  submitting.value = true
  try {
    const response = await api.post<BulkImportResponse>('/articles/bulk-import/', { urls })
    batchId.value = response.data.batch_id
    logger.info('bulk_import_started', { batchId: response.data.batch_id, total: response.data.total })
    startPolling()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Bulk import failed: ${detail}`, 'error')
    logger.error('bulk_import_failed', { detail: String(e) })
  } finally {
    submitting.value = false
  }
}

function startPolling() {
  pollStatus()
  pollTimer = setInterval(pollStatus, 2000)
}

async function pollStatus() {
  if (!batchId.value) return
  try {
    const response = await api.get<BulkImportStatus>(`/articles/bulk-import/${batchId.value}/`)
    batch.value = response.data
    if (response.data.status === 'completed') {
      stopPolling()
      logger.info('bulk_import_completed', {
        batchId: batchId.value,
        succeeded: response.data.succeeded,
        failed: response.data.failed_count,
      })
    }
  } catch {
    logger.error('bulk_import_poll_failed', { batchId: batchId.value })
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function resetForm() {
  stopPolling()
  batchId.value = ''
  batch.value = null
  urlText.value = ''
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.bulk-import__status {
  font-size: var(--fs-500);
  font-weight: bold;
}
</style>
