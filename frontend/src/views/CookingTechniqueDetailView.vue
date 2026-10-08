<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div
      v-if="loading"
      class="cooking-technique-detail__empty"
    >
      Loading...
    </div>

    <div
      v-else-if="!technique"
      class="cooking-technique-detail__empty"
    >
      Technique not found.
    </div>

    <div
      v-else
      class="cooking-technique-detail"
      data-testid="cooking-technique-detail"
    >
      <div class="cooking-technique-detail__header">
        <button
          type="button"
          class="button"
          data-testid="cooking-technique-detail-back"
          @click="$router.push('/recipes/cooking-techniques')"
        >
          <span class="button__text">← Back</span>
        </button>
        <h1 class="cooking-technique-detail__title">{{ technique.name }}</h1>
        <div class="cooking-technique-detail__header-actions">
          <button
            type="button"
            class="button button--warning"
            data-testid="cooking-technique-detail-edit"
            @click="showModal = true"
          >
            <span class="button__text">Edit</span>
          </button>
        </div>
      </div>

      <div class="cooking-technique-detail__meta">
        <span><strong>Category:</strong> {{ categoryLabel(technique.category) }}</span>
        <span v-if="technique.rating"><strong>Rating:</strong> {{ technique.rating }}/5</span>
        <span
          v-if="technique.source_url"
          class="cooking-technique-detail__source"
          ><strong>Source:</strong>
          <a
            :href="technique.source_url"
            target="_blank"
            rel="noopener noreferrer"
            >{{ technique.source_name ?? technique.source_url }}</a
          >
        </span>
      </div>

      <div
        v-if="technique.tags && technique.tags.length > 0"
        class="cooking-technique-detail__tags"
      >
        <span
          v-for="tag in technique.tags"
          :key="tag"
          class="cooking-technique-detail__tag"
          >{{ tag }}</span
        >
      </div>

      <p class="cooking-technique-detail__summary">{{ technique.summary }}</p>

      <section class="cooking-technique-detail__section">
        <h2>Technique</h2>
        <div
          class="cooking-technique-detail__body markdown-body"
          data-testid="cooking-technique-detail-body"
          v-html="renderedBody"
        ></div>
      </section>

      <section
        v-if="technique.why_it_works"
        class="cooking-technique-detail__section"
      >
        <h2>Why It Works</h2>
        <div
          class="markdown-body"
          v-html="renderedWhy"
        ></div>
      </section>

      <section
        v-if="technique.common_pitfalls"
        class="cooking-technique-detail__section"
      >
        <h2>Common Pitfalls</h2>
        <div
          class="markdown-body"
          v-html="renderedPitfalls"
        ></div>
      </section>

      <AddEditCookingTechniqueModal
        :visible="showModal"
        :edit-data="technique"
        @close="showModal = false"
        @update="handleUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSubnav from '@/components/AppSubnav.vue'
import AddEditCookingTechniqueModal from '@/components/recipes/AddEditCookingTechniqueModal.vue'
import { useCookingTechniquesStore } from '@/stores/cookingTechniques'
import { useNotifications } from '@/composables/useNotifications'
import { renderMarkdown } from '@/utils/markdown'
import { ApiError } from '@/api/errors'
import type { CookingTechnique } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const route = useRoute()
const store = useCookingTechniquesStore()
const { show: notify } = useNotifications()

const technique = ref<CookingTechnique | null>(null)
const loading = ref(true)
const showModal = ref(false)

const renderedBody = computed(() => (technique.value ? renderMarkdown(technique.value.body) : ''))
const renderedWhy = computed(() => (technique.value?.why_it_works ? renderMarkdown(technique.value.why_it_works) : ''))
const renderedPitfalls = computed(() => (technique.value?.common_pitfalls ? renderMarkdown(technique.value.common_pitfalls) : ''))

const CATEGORY_LABELS: Record<string, string> = {
  heat_application: 'Heat application',
  flavor_development: 'Flavor development',
  emulsion_and_texture: 'Emulsion & texture',
  preservation_and_pre_treatment: 'Preservation & pre-treatment',
  seasoning_and_finishing: 'Seasoning & finishing',
  dough_and_batter: 'Dough & batter',
  knife_work_and_prep: 'Knife work & prep',
  composition_and_ratio: 'Composition & ratio',
  equipment_technique: 'Equipment technique',
}

function categoryLabel(value: string): string {
  return CATEGORY_LABELS[value] ?? value
}

async function loadTechnique(slug: string) {
  loading.value = true
  try {
    technique.value = await store.fetchBySlug(slug)
  } catch (e) {
    technique.value = null
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to load technique: ${detail}`, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const slug = route.params.slug as string
  if (slug) loadTechnique(slug)
})

watch(
  () => route.params.slug,
  (newSlug) => {
    if (typeof newSlug === 'string' && newSlug) loadTechnique(newSlug)
  }
)

async function handleUpdate(id: number, data: Parameters<typeof store.update>[1]) {
  try {
    const updated = await store.update(id, data)
    technique.value = updated
    showModal.value = false
    notify(`${updated.name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.cooking-technique-detail {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-m);
}

.cooking-technique-detail__header {
  display: flex;
  align-items: center;
  gap: var(--space-m);
  margin-bottom: var(--space-m);
}

.cooking-technique-detail__title {
  flex: 1;
  margin: 0;
}

.cooking-technique-detail__header-actions {
  display: flex;
  gap: var(--space-xs);
}

.cooking-technique-detail__meta {
  display: flex;
  gap: var(--space-m);
  flex-wrap: wrap;
  margin-bottom: var(--space-s);
  font-size: var(--fs-300);
}

.cooking-technique-detail__tags {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: var(--space-m);
}

.cooking-technique-detail__tag {
  padding: 2px 10px;
  border-radius: var(--border-radius);
  background: var(--clr-gray-200);
  font-size: var(--fs-200);
}

.cooking-technique-detail__summary {
  font-style: italic;
  font-size: var(--fs-400);
  margin-bottom: var(--space-m);
  padding: var(--space-s) var(--space-m);
  border-left: 3px solid var(--clr-accent);
}

.cooking-technique-detail__section {
  margin-bottom: var(--space-l);
}

.cooking-technique-detail__section h2 {
  margin-bottom: var(--space-xs);
}

.cooking-technique-detail__empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-l);
  text-align: center;
}
</style>
