<template>
  <div
    class="recipe-candidate"
    data-testid="recipe-candidate"
  >
    <div class="recipe-candidate__header">
      <h3 class="recipe-candidate__title">{{ candidate.name }}</h3>
      <span
        v-if="candidate.total_time_minutes"
        class="recipe-candidate__time"
        >{{ candidate.total_time_minutes }} min</span
      >
    </div>
    <p
      v-if="candidate.description"
      class="recipe-candidate__description"
    >
      {{ candidate.description }}
    </p>
    <div class="recipe-candidate__meta">
      <span v-if="candidate.cuisine">{{ candidate.cuisine }}</span>
      <span v-if="candidate.meal_type">{{ candidate.meal_type }}</span>
      <span v-if="candidate.difficulty">{{ candidate.difficulty }}</span>
      <span>{{ candidate.servings }} servings</span>
    </div>
    <details class="recipe-candidate__details">
      <summary>{{ candidate.ingredients.length }} ingredients</summary>
      <ul class="recipe-candidate__ingredients">
        <li
          v-for="(ing, idx) in candidate.ingredients"
          :key="idx"
        >
          <span v-if="ing.quantity">{{ ing.quantity }}</span>
          <span v-if="ing.unit">{{ formatUnit(ing.unit) }}</span>
          <span>{{ ing.item }}</span>
          <span
            v-if="ing.prep_note"
            class="recipe-candidate__prep"
            >, {{ ing.prep_note }}</span
          >
        </li>
      </ul>
    </details>
    <a
      :href="candidate.source_url"
      target="_blank"
      rel="noopener"
      class="recipe-candidate__source"
      >{{ candidate.source_name || 'View source' }}</a
    >
    <div
      v-if="!hideActions"
      class="recipe-candidate__actions"
    >
      <button
        type="button"
        class="button"
        data-testid="recipe-candidate-save"
        @click="$emit('save', candidate)"
      >
        <span class="button__text">Save to Recipes</span>
      </button>
      <button
        type="button"
        class="button button--danger"
        data-testid="recipe-candidate-dismiss"
        @click="$emit('dismiss', candidate)"
      >
        <span class="button__text button__text--danger">Dismiss</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RecipeCandidate } from '@/api/client'

withDefaults(defineProps<{ candidate: RecipeCandidate; hideActions?: boolean }>(), { hideActions: false })
defineEmits<{
  save: [candidate: RecipeCandidate]
  dismiss: [candidate: RecipeCandidate]
}>()

function formatUnit(unit: string | null): string {
  if (!unit) return ''
  if (unit === 'to_taste') return 'to taste'
  if (unit === 'fl_oz') return 'fl oz'
  return unit
}
</script>

<style scoped>
.recipe-candidate {
  padding: var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.recipe-candidate__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-s);
}

.recipe-candidate__title {
  font-size: var(--fs-500);
  margin: 0;
}

.recipe-candidate__time {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
}

.recipe-candidate__description {
  margin: 0;
  color: var(--clr-text);
  font-size: var(--fs-400);
}

.recipe-candidate__meta {
  display: flex;
  gap: var(--space-s);
  flex-wrap: wrap;
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  text-transform: capitalize;
}

.recipe-candidate__details summary {
  cursor: pointer;
  font-size: var(--fs-300);
}

.recipe-candidate__ingredients {
  list-style: none;
  padding-left: var(--space-s);
  margin-top: var(--space-xs);
}

.recipe-candidate__ingredients li {
  font-size: var(--fs-300);
  display: flex;
  gap: var(--space-3xs);
  flex-wrap: wrap;
}

.recipe-candidate__prep {
  color: var(--clr-gray-400);
  font-style: italic;
}

.recipe-candidate__source {
  color: var(--clr-accent-light);
  text-decoration: underline;
  font-size: var(--fs-300);
}

.recipe-candidate__actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
</style>
