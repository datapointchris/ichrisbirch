<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column">
      <div class="grid__item">
        <h1 class="ai-suggest__title">Recipe Discovery</h1>
        <p class="ai-suggest__subtitle">Describe what you have and what you want — Claude will search the web for matching recipes.</p>
      </div>
    </div>

    <div class="grid grid--one-column">
      <div class="grid__item">
        <form
          class="ai-suggest__form"
          @submit.prevent="handleSuggest"
        >
          <div class="add-edit-modal__form-item">
            <label for="ai-have">Ingredients you have (comma-separated)</label>
            <input
              id="ai-have"
              v-model="haveInput"
              type="text"
              class="textbox"
              placeholder="chicken, lemon, pasta"
              data-testid="ai-suggest-have-input"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="ai-want">What do you want? (free-form)</label>
            <input
              id="ai-want"
              v-model="wantInput"
              type="text"
              class="textbox"
              placeholder="weeknight dinner, low-carb, high protein"
              data-testid="ai-suggest-want-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="ai-count">How many suggestions?</label>
            <input
              id="ai-count"
              v-model.number="countInput"
              type="number"
              min="1"
              max="5"
              class="textbox add-edit-modal__number-input"
              data-testid="ai-suggest-count-input"
            />
          </div>

          <div class="add-edit-modal__form-buttons">
            <button
              type="submit"
              class="button"
              data-testid="ai-suggest-submit"
              :disabled="store.aiLoading || !haveInput.trim()"
            >
              <span class="button__text">{{ store.aiLoading ? 'Searching...' : 'Find Recipes' }}</span>
            </button>
            <button
              v-if="store.aiCandidates.length > 0"
              type="button"
              class="button button--danger"
              data-testid="ai-suggest-clear"
              @click="store.clearAICandidates"
            >
              <span class="button__text button__text--danger">Clear</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="store.aiLoading"
      class="ai-suggest__loading"
    >
      Searching the web and evaluating recipes... (this may take 30-60 seconds)
    </div>

    <div
      v-if="store.aiCandidates.length > 0"
      class="ai-suggest__results"
      data-testid="ai-suggest-results"
    >
      <RecipeCandidateCard
        v-for="candidate in store.aiCandidates"
        :key="candidate.source_url"
        :candidate="candidate"
        @save="handleSave"
        @dismiss="handleDismiss"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSubnav from '@/components/AppSubnav.vue'
import RecipeCandidateCard from '@/components/recipes/RecipeCandidateCard.vue'
import { useRecipesStore } from '@/stores/recipes'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { RecipeCandidate } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const store = useRecipesStore()
const { show: notify } = useNotifications()

const haveInput = ref('')
const wantInput = ref('')
const countInput = ref(3)

async function handleSuggest() {
  const have = haveInput.value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  if (have.length === 0) return
  try {
    await store.aiSuggest({
      have,
      want: wantInput.value.trim() || null,
      count: countInput.value,
    })
    notify(`Found ${store.aiCandidates.length} candidates`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Suggestion failed: ${detail}`, 'error')
  }
}

async function handleSave(candidate: RecipeCandidate) {
  try {
    const saved = await store.aiSave(candidate)
    notify(`${saved.name} added to recipes`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Save failed: ${detail}`, 'error')
  }
}

function handleDismiss(candidate: RecipeCandidate) {
  store.aiCandidates = store.aiCandidates.filter((c) => c.source_url !== candidate.source_url)
}
</script>

<style scoped>
.ai-suggest__title {
  font-size: var(--fs-700);
  margin-bottom: var(--space-xs);
}

.ai-suggest__subtitle {
  color: var(--clr-gray-400);
  margin-bottom: var(--space-m);
}

.ai-suggest__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-s);
}

.ai-suggest__loading {
  text-align: center;
  padding: var(--space-l);
  color: var(--clr-accent-light);
  font-style: italic;
}

.ai-suggest__results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--space-m);
  padding-inline: var(--space-m);
}
</style>
