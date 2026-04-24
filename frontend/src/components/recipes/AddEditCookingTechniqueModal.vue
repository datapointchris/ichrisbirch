<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="nameInput"
    @close="handleModalClose"
  >
    <template #default="{ handleSuccess }">
      <form
        class="add-edit-modal__form cooking-technique-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Cooking Technique' : 'Add Cooking Technique' }}</h2>

        <!-- name -->
        <div class="add-edit-modal__form-item">
          <label for="ct-name">Name</label>
          <input
            id="ct-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="cooking-technique-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <!-- category, rating -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="ct-category">Category</label>
            <NeuSelect
              :model-value="form.category"
              :options="categoryOptions"
              data-testid="cooking-technique-category-input"
              @update:model-value="form.category = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="ct-rating">Rating (1-5)</label>
            <input
              id="ct-rating"
              v-model="form.rating"
              data-testid="cooking-technique-rating-input"
              type="number"
              class="textbox"
              min="1"
              max="5"
              step="1"
            />
          </div>
        </div>

        <!-- summary -->
        <div class="add-edit-modal__form-item">
          <label for="ct-summary">Summary (one-paragraph TL;DR)</label>
          <textarea
            id="ct-summary"
            v-model="form.summary"
            data-testid="cooking-technique-summary-input"
            class="textbox"
            rows="3"
            required
          ></textarea>
        </div>

        <!-- body -->
        <div class="add-edit-modal__form-item">
          <label for="ct-body">Body (markdown)</label>
          <textarea
            id="ct-body"
            v-model="form.body"
            data-testid="cooking-technique-body-input"
            class="textbox"
            rows="10"
            required
          ></textarea>
        </div>

        <!-- why_it_works -->
        <div class="add-edit-modal__form-item">
          <label for="ct-why">Why It Works (optional)</label>
          <textarea
            id="ct-why"
            v-model="form.why_it_works"
            data-testid="cooking-technique-why-input"
            class="textbox"
            rows="3"
          ></textarea>
        </div>

        <!-- common_pitfalls -->
        <div class="add-edit-modal__form-item">
          <label for="ct-pitfalls">Common Pitfalls (optional)</label>
          <textarea
            id="ct-pitfalls"
            v-model="form.common_pitfalls"
            data-testid="cooking-technique-pitfalls-input"
            class="textbox"
            rows="3"
          ></textarea>
        </div>

        <!-- source -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="ct-source-url">Source URL</label>
            <input
              id="ct-source-url"
              v-model="form.source_url"
              data-testid="cooking-technique-source-url-input"
              type="url"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="ct-source-name">Source Name</label>
            <input
              id="ct-source-name"
              v-model="form.source_name"
              data-testid="cooking-technique-source-name-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- tags -->
        <div class="add-edit-modal__form-item">
          <label for="ct-tags">Tags (comma-separated)</label>
          <input
            id="ct-tags"
            v-model="form.tags"
            data-testid="cooking-technique-tags-input"
            type="text"
            class="textbox"
            placeholder="e.g. sauce, emulsion, framework"
          />
        </div>

        <div class="add-edit-modal__form-actions">
          <button
            type="submit"
            class="button"
            :disabled="!canSubmit"
            data-testid="cooking-technique-submit-button"
          >
            <span class="button__text">{{ editData ? 'Save' : 'Add' }}</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import AddEditModal from '@/components/AddEditModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import type { CookingTechnique, CookingTechniqueCreate, CookingTechniqueUpdate } from '@/api/client'

const props = defineProps<{
  visible: boolean
  editData?: CookingTechnique | null
}>()

const emit = defineEmits<{
  close: []
  create: [payload: CookingTechniqueCreate]
  update: [id: number, payload: CookingTechniqueUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const categoryOptions = [
  { value: '', label: '— Choose Category —' },
  { value: 'heat_application', label: 'Heat application' },
  { value: 'flavor_development', label: 'Flavor development' },
  { value: 'emulsion_and_texture', label: 'Emulsion & texture' },
  { value: 'preservation_and_pre_treatment', label: 'Preservation & pre-treatment' },
  { value: 'seasoning_and_finishing', label: 'Seasoning & finishing' },
  { value: 'dough_and_batter', label: 'Dough & batter' },
  { value: 'knife_work_and_prep', label: 'Knife work & prep' },
  { value: 'composition_and_ratio', label: 'Composition & ratio' },
  { value: 'equipment_technique', label: 'Equipment technique' },
]

function createEmptyForm() {
  return {
    name: '',
    category: '',
    summary: '',
    body: '',
    why_it_works: '',
    common_pitfalls: '',
    source_url: '',
    source_name: '',
    tags: '',
    rating: '',
  }
}

const form = reactive(createEmptyForm())

const canSubmit = computed(() => {
  return form.name.trim() !== '' && form.category.trim() !== '' && form.summary.trim() !== '' && form.body.trim() !== ''
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const t = props.editData
      form.name = t.name
      form.category = t.category
      form.summary = t.summary
      form.body = t.body
      form.why_it_works = t.why_it_works ?? ''
      form.common_pitfalls = t.common_pitfalls ?? ''
      form.source_url = t.source_url ?? ''
      form.source_name = t.source_name ?? ''
      form.tags = (t.tags ?? []).join(', ')
      form.rating = t.rating != null ? String(t.rating) : ''
    } else if (val && !props.editData) {
      Object.assign(form, createEmptyForm())
    }
  }
)

function resetForm() {
  Object.assign(form, createEmptyForm())
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function buildPayload() {
  const tags = form.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  const emptyVal = props.editData ? null : undefined
  return {
    name: form.name.trim(),
    category: form.category,
    summary: form.summary.trim(),
    body: form.body,
    why_it_works: form.why_it_works.trim() || emptyVal,
    common_pitfalls: form.common_pitfalls.trim() || emptyVal,
    source_url: form.source_url.trim() || emptyVal,
    source_name: form.source_name.trim() || emptyVal,
    tags: tags.length > 0 ? tags : emptyVal,
    rating: form.rating ? Number(form.rating) : emptyVal,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!canSubmit.value) return
  const payload = buildPayload()
  if (props.editData) {
    emit('update', props.editData.id, payload as CookingTechniqueUpdate)
  } else {
    emit('create', payload as CookingTechniqueCreate)
  }
  handleSuccess()
}
</script>

<style scoped>
.cooking-technique-modal__form textarea.textbox {
  font-family: var(--ff-mono, monospace);
  font-size: var(--fs-300);
  resize: vertical;
}
</style>
