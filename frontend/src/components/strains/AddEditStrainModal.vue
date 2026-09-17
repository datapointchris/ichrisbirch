<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="nameInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Strain' : 'Add Strain' }}</h2>

        <!-- name -->
        <div class="add-edit-modal__form-item">
          <label for="strain-name">Name</label>
          <input
            id="strain-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="strain-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <!-- type, status -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="strain-type">Type</label>
            <NeuSelect
              :model-value="form.strain_type"
              :options="typeOptions"
              data-testid="strain-type-input"
              @update:model-value="form.strain_type = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="strain-status">Status</label>
            <NeuSelect
              :model-value="form.status"
              :options="statusOptions"
              data-testid="strain-status-input"
              @update:model-value="form.status = $event"
            />
          </div>
        </div>

        <!-- breeder, lineage -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="strain-breeder">Breeder</label>
            <input
              id="strain-breeder"
              v-model="form.breeder"
              data-testid="strain-breeder-input"
              type="text"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="strain-lineage">Lineage</label>
            <input
              id="strain-lineage"
              v-model="form.lineage"
              data-testid="strain-lineage-input"
              type="text"
              class="textbox"
              placeholder="Blueberry x Haze"
            />
          </div>
        </div>

        <!-- thc, cbd, rating -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="strain-thc">THC %</label>
            <input
              id="strain-thc"
              v-model="form.thc_percent"
              data-testid="strain-thc-input"
              type="number"
              class="textbox add-edit-modal__number-input"
              min="0"
              max="100"
              step="any"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="strain-cbd">CBD %</label>
            <input
              id="strain-cbd"
              v-model="form.cbd_percent"
              data-testid="strain-cbd-input"
              type="number"
              class="textbox add-edit-modal__number-input"
              min="0"
              max="100"
              step="any"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="strain-rating">Rating (1-10)</label>
            <input
              id="strain-rating"
              v-model="form.rating"
              data-testid="strain-rating-input"
              type="number"
              class="textbox add-edit-modal__number-input"
              min="1"
              max="10"
              step="1"
            />
          </div>
        </div>

        <!-- effects, flavors, terpenes -->
        <div
          v-for="group in chipGroups"
          :key="group.key"
          class="add-edit-modal__form-item"
        >
          <label>{{ group.label }}</label>
          <div class="strain-chips">
            <button
              v-for="chip in group.chips"
              :key="chip.name"
              type="button"
              class="strain-chips__chip"
              :class="{
                'strain-chips__chip--on': group.selected.includes(chip.name),
                'strain-chips__chip--undefined': chip.orphan,
              }"
              :data-testid="`strain-${group.key}-${chip.name}`"
              :title="chip.orphan ? 'Not in the vocabulary — click to remove it' : undefined"
              @click="toggle(group.selected, chip.name)"
            >
              {{ chip.name }}
            </button>
            <span
              v-if="group.chips.length === 0"
              class="strains__empty"
              >No {{ group.label.toLowerCase() }} defined.</span
            >
          </div>
        </div>

        <!-- source, last tried -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="strain-source">Source</label>
            <input
              id="strain-source"
              v-model="form.source"
              data-testid="strain-source-input"
              type="text"
              class="textbox"
              placeholder="Dispensary or shop"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="strain-last-tried">Last Tried</label>
            <DatePicker
              id="strain-last-tried"
              data-testid="strain-last-tried-input"
              :model-value="form.last_tried_date"
              @update:model-value="form.last_tried_date = $event"
            />
          </div>
        </div>

        <!-- tags -->
        <div class="add-edit-modal__form-item">
          <label for="strain-tags">Tags (comma-separated)</label>
          <input
            id="strain-tags"
            v-model="form.tags"
            data-testid="strain-tags-input"
            type="text"
            class="textbox"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="strain-notes">Notes</label>
          <textarea
            id="strain-notes"
            v-model="form.notes"
            data-testid="strain-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="strain-review">Review</label>
          <textarea
            id="strain-review"
            v-model="form.review"
            data-testid="strain-review-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="strain-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Strain</span>
          </button>
          <button
            type="button"
            data-testid="strain-cancel-button"
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
import { computed, reactive, ref, watch } from 'vue'
import type { Strain, StrainCreate, StrainUpdate } from '@/api/client'
import { useStrainsStore, STRAIN_STATUS_LABELS, humanizeStrainValue as humanize } from '@/stores/strains'
import AddEditModal from '@/components/AddEditModal.vue'
import DatePicker from '@/components/DatePicker.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const props = defineProps<{
  visible: boolean
  editData?: Strain | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: StrainCreate]
  update: [id: number, data: StrainUpdate]
}>()

const store = useStrainsStore()
const nameInput = ref<HTMLInputElement | null>(null)

// Every option comes from the fetched vocabulary, so a value added to a lookup
// table on the server shows up here without this file changing.
const typeOptions = computed(() => [
  { value: '', label: '— none —' },
  ...store.vocabulary.strain_type.map((t) => ({ value: t.name, label: humanize(t.name) })),
])

const statusOptions = computed(() =>
  store.vocabulary.status.map((s) => ({
    value: s.name,
    label: STRAIN_STATUS_LABELS[s.name as keyof typeof STRAIN_STATUS_LABELS] ?? humanize(s.name),
  }))
)

function createEmptyForm() {
  return {
    name: '',
    breeder: '',
    lineage: '',
    strain_type: '',
    status: 'want_to_try',
    thc_percent: '',
    cbd_percent: '',
    rating: '',
    effects: [] as string[],
    flavors: [] as string[],
    terpenes: [] as string[],
    tags: '',
    source: '',
    notes: '',
    review: '',
    last_tried_date: '',
  }
}

const form = reactive(createEmptyForm())

/**
 * A chip for every vocabulary value, plus one for any value the strain carries
 * that the vocabulary does not define.
 *
 * That second group is what keeps such a strain editable. The payload resends
 * the whole array, and the API refuses a value outside the vocabulary, so a
 * value with no chip is one the form can neither keep nor remove — and the
 * record cannot be saved at all. An undefined value renders marked, and
 * clicking it off is the way out.
 */
function chipsFor(entries: { name: string }[], selected: string[]) {
  const known = entries.map((entry) => ({ name: entry.name, orphan: false }))
  const orphans = selected.filter((value) => !entries.some((entry) => entry.name === value)).map((name) => ({ name, orphan: true }))
  return [...known, ...orphans]
}

const chipGroups = computed(() => [
  { key: 'effect', label: 'Effects', chips: chipsFor(store.vocabulary.effects, form.effects), selected: form.effects },
  { key: 'flavor', label: 'Flavors', chips: chipsFor(store.vocabulary.flavors, form.flavors), selected: form.flavors },
  { key: 'terpene', label: 'Terpenes', chips: chipsFor(store.vocabulary.terpenes, form.terpenes), selected: form.terpenes },
])

function toggle(selected: string[], value: string) {
  const index = selected.indexOf(value)
  if (index === -1) {
    selected.push(value)
  } else {
    selected.splice(index, 1)
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const strain = props.editData
      form.name = strain.name
      form.breeder = strain.breeder ?? ''
      form.lineage = strain.lineage ?? ''
      form.strain_type = strain.strain_type ?? ''
      form.status = strain.status
      form.thc_percent = strain.thc_percent != null ? String(strain.thc_percent) : ''
      form.cbd_percent = strain.cbd_percent != null ? String(strain.cbd_percent) : ''
      form.rating = strain.rating != null ? String(strain.rating) : ''
      form.effects = [...strain.effects]
      form.flavors = [...strain.flavors]
      form.terpenes = [...strain.terpenes]
      form.tags = strain.tags.join(', ')
      form.source = strain.source ?? ''
      form.notes = strain.notes ?? ''
      form.review = strain.review ?? ''
      form.last_tried_date = strain.last_tried_date ?? ''
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
  // An edit sends an explicit null to clear a column; a create omits the key so
  // the server default applies. The arrays always travel, because a chip
  // deselected on an edit has to reach the server as the shorter list.
  const emptyVal = props.editData ? null : undefined
  return {
    name: form.name.trim(),
    breeder: form.breeder.trim() || emptyVal,
    lineage: form.lineage.trim() || emptyVal,
    strain_type: form.strain_type || emptyVal,
    status: form.status,
    thc_percent: form.thc_percent !== '' ? Number(form.thc_percent) : emptyVal,
    cbd_percent: form.cbd_percent !== '' ? Number(form.cbd_percent) : emptyVal,
    rating: form.rating !== '' ? Number(form.rating) : emptyVal,
    effects: [...form.effects],
    flavors: [...form.flavors],
    terpenes: [...form.terpenes],
    tags: form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean),
    source: form.source.trim() || emptyVal,
    notes: form.notes.trim() || emptyVal,
    review: form.review.trim() || emptyVal,
    last_tried_date: form.last_tried_date || emptyVal,
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (props.editData) {
    emit('update', props.editData.id, buildPayload() as StrainUpdate)
  } else {
    emit('create', buildPayload() as StrainCreate)
  }
  handleSuccess()
}
</script>
