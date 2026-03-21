<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="editData ? titleInput : urlInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Article' : 'Add Article' }}</h2>

        <div
          v-if="!editData"
          class="add-edit-modal__form-item"
        >
          <label for="article-url">URL</label>
          <div class="add-edit-modal__form-row">
            <input
              id="article-url"
              ref="urlInput"
              v-model="form.url"
              data-testid="article-url-input"
              type="url"
              class="textbox"
              required
            />
            <button
              type="button"
              data-testid="article-auto-populate-button"
              class="button"
              :disabled="!form.url.trim() || summarizing"
              @click="handleAutoPopulate"
            >
              <span class="button__text">{{ summarizing ? 'Summarizing...' : 'Auto Populate' }}</span>
            </button>
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="article-title">Title</label>
          <input
            id="article-title"
            ref="titleInput"
            v-model="form.title"
            data-testid="article-title-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="article-tags">Tags (comma-separated)</label>
          <input
            id="article-tags"
            v-model="form.tags"
            data-testid="article-tags-input"
            type="text"
            class="textbox"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="article-summary">Summary</label>
          <textarea
            id="article-summary"
            v-model="form.summary"
            data-testid="article-summary-input"
            rows="6"
            class="textbox"
            required
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="article-notes">Notes</label>
          <textarea
            id="article-notes"
            v-model="form.notes"
            data-testid="article-notes-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="article-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Article</span>
          </button>
          <button
            type="button"
            data-testid="article-cancel-button"
            class="button button--danger"
            @click="handleClose()"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { ArticleCreate, ArticleUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const store = useArticlesStore()
const { show: notify } = useNotifications()
const summarizing = ref(false)

const props = defineProps<{
  visible: boolean
  editData?: {
    id: number
    title: string
    url: string
    tags: string[]
    summary: string
    notes?: string
  } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: ArticleCreate]
  update: [id: number, data: ArticleUpdate]
}>()

const urlInput = ref<HTMLInputElement | null>(null)
const titleInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  url: '',
  title: '',
  tags: '',
  summary: '',
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.url = props.editData.url
      form.title = props.editData.title
      form.tags = props.editData.tags.join(', ')
      form.summary = props.editData.summary
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.url = ''
  form.title = ''
  form.tags = ''
  form.summary = ''
  form.notes = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function parseTags(tagsStr: string): string[] {
  return tagsStr
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
}

async function handleAutoPopulate() {
  if (!form.url.trim()) return
  summarizing.value = true
  try {
    const result = await store.summarizeUrl(form.url.trim())
    form.title = result.title
    form.summary = result.summary
    form.tags = result.tags.join(', ')
    notify('Article info populated from URL', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Auto-populate failed: ${detail}`, 'error')
  } finally {
    summarizing.value = false
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.title.trim() || !form.summary.trim()) return
  if (!props.editData && !form.url.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, {
      title: form.title.trim(),
      tags: parseTags(form.tags),
      summary: form.summary.trim(),
      notes: form.notes.trim() || undefined,
    })
  } else {
    emit('create', {
      url: form.url.trim(),
      title: form.title.trim(),
      tags: parseTags(form.tags),
      summary: form.summary.trim(),
      notes: form.notes.trim() || undefined,
      save_date: new Date().toISOString(),
    })
  }
  handleSuccess()
}
</script>
