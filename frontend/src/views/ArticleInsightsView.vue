<template>
  <div>
    <ArticlesSubnav />

    <div class="grid grid--one-column">
      <div class="add-item-wrapper">
        <h3>URL</h3>
        <form
          class="add-item-form"
          @submit.prevent="handleSubmit"
        >
          <div class="add-item-form__item add-item-form__item--full-width">
            <input
              id="url"
              v-model="url"
              type="url"
              class="textbox"
              placeholder="Enter article or YouTube URL..."
              required
            />
            <button
              type="submit"
              class="button"
              :disabled="processing"
            >
              <span class="button__text">{{ processing ? 'Processing...' : 'Educate Me!' }}</span>
            </button>
          </div>
          <div
            v-if="elapsed"
            class="add-item-form__item add-item-form__item--full-width"
          >
            Elapsed Time: {{ elapsed }}
          </div>
        </form>
      </div>
      <div
        v-if="insightsHtml"
        class="article-insight"
        v-html="insightsHtml"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { useNotifications } from '@/composables/useNotifications'
import { createLogger } from '@/utils/logger'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'

const logger = createLogger('ArticleInsights')
const { show: notify } = useNotifications()

const url = ref('')
const insightsHtml = ref('')
const processing = ref(false)
const elapsed = ref('')

async function handleSubmit() {
  if (!url.value.trim()) return
  processing.value = true
  insightsHtml.value = ''
  elapsed.value = ''
  const startTime = Date.now()

  try {
    const response = await api.post('/articles/insights/', { url: url.value.trim() })
    insightsHtml.value = response.data as string
    const seconds = ((Date.now() - startTime) / 1000).toFixed(1)
    elapsed.value = `${seconds}s`
    logger.info('insights_generated', { url: url.value })
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Insights failed: ${detail}`, 'error')
    logger.error('insights_failed', { url: url.value })
  } finally {
    processing.value = false
  }
}
</script>
