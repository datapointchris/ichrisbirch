<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column">
      <div class="grid__item">
        <h1 class="url-import__title">Import from URL</h1>
        <p class="url-import__subtitle">
          Paste a YouTube video or article URL. Claude will classify it as a recipe, a technique, or both, and return candidates to review.
        </p>
      </div>
    </div>

    <div class="grid grid--one-column">
      <div class="grid__item">
        <form
          class="url-import__form"
          @submit.prevent="handleImport"
        >
          <div class="add-edit-modal__form-item">
            <label for="url-input">URL</label>
            <input
              id="url-input"
              v-model="urlInput"
              type="url"
              class="textbox"
              placeholder="https://www.youtube.com/watch?v=..."
              data-testid="url-import-url-input"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label>Kind</label>
            <div class="url-import__hint-group">
              <label
                v-for="opt in hintOptions"
                :key="opt.value"
                class="url-import__hint-option"
              >
                <input
                  v-model="hintInput"
                  type="radio"
                  :value="opt.value"
                  :data-testid="`url-import-hint-${opt.value}`"
                />
                {{ opt.label }}
              </label>
            </div>
          </div>

          <div class="add-edit-modal__form-buttons">
            <button
              type="submit"
              class="button"
              data-testid="url-import-submit"
              :disabled="store.urlImportLoading || !urlInput.trim()"
            >
              <span class="button__text">{{ store.urlImportLoading ? 'Classifying...' : 'Import' }}</span>
            </button>
            <button
              v-if="store.urlImportCandidate"
              type="button"
              class="button button--danger"
              data-testid="url-import-clear"
              @click="store.clearUrlImportCandidate"
            >
              <span class="button__text button__text--danger">Clear</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="store.urlImportLoading"
      class="url-import__loading"
    >
      Fetching content and classifying... (this may take 15-45 seconds for YouTube videos)
    </div>

    <div
      v-if="store.urlImportCandidate"
      class="url-import__result"
      data-testid="url-import-result"
    >
      <div class="url-import__result-header">
        <span
          class="url-import__kind-badge"
          :data-kind="store.urlImportCandidate.kind"
          :data-testid="`url-import-kind-${store.urlImportCandidate.kind}`"
        >
          {{ kindLabel(store.urlImportCandidate.kind) }}
        </span>
        <button
          type="button"
          class="button"
          data-testid="url-import-save"
          :disabled="saving"
          @click="handleSave"
        >
          <span class="button__text">{{ saving ? 'Saving...' : saveButtonLabel }}</span>
        </button>
      </div>

      <section
        v-if="store.urlImportCandidate.recipe"
        class="url-import__section"
        data-testid="url-import-recipe-section"
      >
        <h2 class="url-import__section-title">Recipe</h2>
        <RecipeCandidateCard
          :candidate="store.urlImportCandidate.recipe"
          :hide-actions="true"
        />
      </section>

      <section
        v-if="store.urlImportCandidate.technique"
        class="url-import__section"
        data-testid="url-import-technique-section"
      >
        <h2 class="url-import__section-title">Cooking Technique</h2>
        <div class="url-import__technique-card">
          <h3>{{ store.urlImportCandidate.technique.name }}</h3>
          <p class="url-import__technique-category">{{ store.urlImportCandidate.technique.category }}</p>
          <p>{{ store.urlImportCandidate.technique.summary }}</p>
        </div>
      </section>

      <p
        v-if="store.urlImportCandidate.kind === 'both' && store.urlImportCandidate.technique_mention"
        class="url-import__mention"
        data-testid="url-import-mention"
      >
        <strong>Will append to recipe notes:</strong> {{ store.urlImportCandidate.technique_mention }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppSubnav from '@/components/AppSubnav.vue'
import RecipeCandidateCard from '@/components/recipes/RecipeCandidateCard.vue'
import { useRecipesStore } from '@/stores/recipes'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { UrlImportHint, UrlImportKind } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const store = useRecipesStore()
const { show: notify } = useNotifications()

const urlInput = ref('')
const hintInput = ref<UrlImportHint>('auto')
const saving = ref(false)

const hintOptions: { value: UrlImportHint; label: string }[] = [
  { value: 'auto', label: 'Auto' },
  { value: 'recipe', label: 'Recipe' },
  { value: 'technique', label: 'Technique' },
  { value: 'both', label: 'Both' },
]

const saveButtonLabel = computed(() => {
  const candidate = store.urlImportCandidate
  if (!candidate) return 'Save'
  if (candidate.kind === 'both') return 'Save Recipe + Technique'
  if (candidate.kind === 'recipe') return 'Save Recipe'
  return 'Save Technique'
})

function kindLabel(kind: UrlImportKind): string {
  if (kind === 'both') return 'Recipe + Technique'
  if (kind === 'recipe') return 'Recipe'
  return 'Technique'
}

async function handleImport() {
  try {
    await store.importFromUrl({ url: urlInput.value.trim(), hint: hintInput.value })
    notify(`Classified as ${store.urlImportCandidate?.kind}`, 'success')
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      notify('This URL is already in your catalog', 'warning')
    } else {
      const detail = e instanceof ApiError ? e.userMessage : String(e)
      notify(`Import failed: ${detail}`, 'error')
    }
  }
}

async function handleSave() {
  if (!store.urlImportCandidate) return
  saving.value = true
  try {
    const result = await store.saveUrlImport(store.urlImportCandidate)
    const parts: string[] = []
    if (result.recipe) parts.push(`recipe "${result.recipe.name}"`)
    if (result.technique) parts.push(`technique "${result.technique.name}"`)
    notify(`Saved ${parts.join(' + ')}`, 'success')
    urlInput.value = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Save failed: ${detail}`, 'error')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.url-import__title {
  font-size: var(--fs-700);
  margin-bottom: var(--space-xs);
}

.url-import__subtitle {
  color: var(--clr-gray-400);
  margin-bottom: var(--space-m);
}

.url-import__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-s);
}

.url-import__hint-group {
  display: flex;
  gap: var(--space-m);
  flex-wrap: wrap;
}

.url-import__hint-option {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  cursor: pointer;
}

.url-import__loading {
  text-align: center;
  padding: var(--space-l);
  color: var(--clr-accent-light);
  font-style: italic;
}

.url-import__result {
  padding-inline: var(--space-m);
  padding-top: var(--space-m);
}

.url-import__result-header {
  display: flex;
  align-items: center;
  gap: var(--space-m);
  margin-bottom: var(--space-m);
}

.url-import__kind-badge {
  padding: var(--space-xs) var(--space-s);
  border-radius: var(--border-radius);
  box-shadow: var(--floating-box);
  font-weight: bold;
}

.url-import__section {
  margin-bottom: var(--space-l);
}

.url-import__section-title {
  font-size: var(--fs-600);
  margin-bottom: var(--space-s);
}

.url-import__technique-card {
  padding: var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
}

.url-import__technique-category {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  margin-bottom: var(--space-xs);
}

.url-import__mention {
  padding: var(--space-s);
  border-left: 3px solid var(--clr-accent);
  margin-top: var(--space-m);
}
</style>
