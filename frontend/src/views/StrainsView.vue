<template>
  <div>
    <!-- Info Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="task-layout__info">
        <span
          class="task-layout__count strain--tried strain-filter"
          :class="{ 'strain-filter--active': store.statusFilter === 'tried' }"
          data-testid="strain-filter-tried"
          @click="store.setStatusFilter('tried')"
          >Tried: {{ store.statusCounts.tried }}</span
        >
        <span
          class="task-layout__count strain--want_to_try strain-filter"
          :class="{ 'strain-filter--active': store.statusFilter === 'want_to_try' }"
          data-testid="strain-filter-want-to-try"
          @click="store.setStatusFilter('want_to_try')"
          >Want to Try: {{ store.statusCounts.want_to_try }}</span
        >
        <span
          class="task-layout__count strain--total strain-filter"
          :class="{ 'strain-filter--active': store.statusFilter === 'all' }"
          data-testid="strain-filter-all"
          @click="store.setStatusFilter('all')"
          >Total: {{ store.statusCounts.total }}</span
        >
        <NeuSelect
          :model-value="store.typeFilter"
          :options="typeFilterOptions"
          data-testid="strain-type-filter"
          @update:model-value="store.setTypeFilter($event)"
        />
        <NeuSelect
          :model-value="store.effectFilter"
          :options="effectFilterOptions"
          data-testid="strain-effect-filter"
          @update:model-value="store.setEffectFilter($event)"
        />
      </div>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="strain-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Strain</span>
      </button>
    </div>

    <!-- Strain Table -->
    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="strains__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div class="strains__header">
            <span
              class="strains__sortable"
              @click="store.setSort('name')"
              >Name<span class="strains__sort-indicator">{{ sortIndicator('name') }}</span></span
            >
            <span
              class="strains__sortable"
              @click="store.setSort('strain_type')"
              >Type<span class="strains__sort-indicator">{{ sortIndicator('strain_type') }}</span></span
            >
            <span
              class="strains__sortable"
              @click="store.setSort('thc_percent')"
              >THC<span class="strains__sort-indicator">{{ sortIndicator('thc_percent') }}</span></span
            >
            <span
              class="strains__sortable"
              @click="store.setSort('cbd_percent')"
              >CBD<span class="strains__sort-indicator">{{ sortIndicator('cbd_percent') }}</span></span
            >
            <span
              class="strains__sortable"
              @click="store.setSort('rating')"
              >Rating<span class="strains__sort-indicator">{{ sortIndicator('rating') }}</span></span
            >
            <span
              class="strains__sortable"
              @click="store.setSort('status')"
              >Status<span class="strains__sort-indicator">{{ sortIndicator('status') }}</span></span
            >
            <span>Actions</span>
          </div>

          <template v-if="store.filteredItems.length === 0">
            <div class="strains__empty">No strains match the selected filter.</div>
          </template>

          <template
            v-for="strain in store.filteredItems"
            :key="strain.id"
          >
            <div
              data-testid="strain-item"
              class="strains__row"
              :class="`strain--${strain.status}`"
            >
              <span
                class="strains__name"
                :title="strain.name"
                >{{ strain.name }}</span
              >
              <span>{{ humanize(strain.strain_type) }}</span>
              <span>{{ percent(strain.thc_percent) }}</span>
              <span>{{ percent(strain.cbd_percent) }}</span>
              <span>{{ strain.rating ?? '' }}</span>
              <span>{{ statusLabel(strain.status) }}</span>
              <span class="strains__actions">
                <ActionButton
                  icon="fa-solid fa-chevron-down"
                  title="Toggle details"
                  :rotated="expandedStrainId === strain.id"
                  @click="toggleDetail(strain.id)"
                />
                <ActionButton
                  data-testid="strain-edit-button"
                  icon="fa-solid fa-pen-to-square"
                  variant="warning"
                  title="Edit strain"
                  @click="openEdit(strain)"
                />
                <ActionButton
                  data-testid="strain-delete-button"
                  icon="fa-regular fa-trash-can"
                  variant="danger"
                  title="Delete strain"
                  @click="handleDelete(strain.id, strain.name)"
                />
              </span>
            </div>

            <div
              class="strains__detail"
              :class="{ 'strains__detail--open': expandedStrainId === strain.id }"
            >
              <div
                v-if="strain.breeder"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Breeder</span>
                <span class="strains__detail-field-value">{{ strain.breeder }}</span>
              </div>
              <div
                v-if="strain.lineage"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Lineage</span>
                <span class="strains__detail-field-value">{{ strain.lineage }}</span>
              </div>
              <div
                v-if="strain.rating != null"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Rating</span>
                <span class="strains__detail-field-value">{{ strain.rating }}/10</span>
              </div>
              <div
                v-for="group in chipGroups(strain)"
                :key="group.label"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">{{ group.label }}</span>
                <span class="strains__detail-field-value">
                  <span
                    v-for="value in group.values"
                    :key="value"
                    class="strains__chip"
                    >{{ value }}</span
                  >
                  <span
                    v-if="group.values.length === 0"
                    class="strains__empty"
                    >none recorded</span
                  >
                </span>
              </div>
              <div
                v-if="strain.tags.length > 0"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Tags</span>
                <span class="strains__detail-field-value">{{ strain.tags.join(', ') }}</span>
              </div>
              <div
                v-if="strain.source"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Source</span>
                <span class="strains__detail-field-value">{{ strain.source }}</span>
              </div>
              <div
                v-if="strain.last_tried_date"
                class="strains__detail-field"
              >
                <span class="strains__detail-field-label">Last Tried</span>
                <span class="strains__detail-field-value">{{ formatDate(strain.last_tried_date, 'shortDate') }}</span>
              </div>
              <div
                v-if="strain.notes"
                class="strains__detail-field strains__detail-notes"
              >
                <span class="strains__detail-field-label">Notes</span>
                <span class="strains__detail-field-value">{{ strain.notes }}</span>
              </div>
              <div
                v-if="strain.review"
                class="strains__detail-field strains__detail-notes"
              >
                <span class="strains__detail-field-label">Review</span>
                <span class="strains__detail-field-value">{{ strain.review }}</span>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>

    <AddEditStrainModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Strain, StrainCreate, StrainUpdate } from '@/api/client'
import { useStrainsStore, STRAIN_STATUS_LABELS, humanizeStrainValue as humanize } from '@/stores/strains'
import { useNotifications } from '@/composables/useNotifications'
import { formatDate } from '@/composables/formatDate'
import { ApiError } from '@/api/errors'
import ActionButton from '@/components/ActionButton.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import AddEditStrainModal from '@/components/strains/AddEditStrainModal.vue'

const store = useStrainsStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<Strain | null>(null)
const expandedStrainId = ref<number | null>(null)

const typeFilterOptions = computed(() => [
  { value: 'all', label: 'All Types' },
  ...store.vocabulary.types.map((t) => ({ value: t.name, label: `${humanize(t.name)} (${t.count})` })),
])

const effectFilterOptions = computed(() => [
  { value: 'all', label: 'All Effects' },
  ...store.vocabulary.effects.map((e) => ({ value: e.name, label: `${humanize(e.name)} (${e.count})` })),
])

function statusLabel(status: string): string {
  return STRAIN_STATUS_LABELS[status as keyof typeof STRAIN_STATUS_LABELS] ?? humanize(status)
}

function percent(value?: number): string {
  return value != null ? `${value}%` : ''
}

function chipGroups(strain: Strain) {
  return [
    { label: 'Effects', values: strain.effects },
    { label: 'Flavors', values: strain.flavors },
    { label: 'Terpenes', values: strain.terpenes },
  ]
}

function sortIndicator(field: string): string {
  if (store.sortField !== field) return ''
  return store.sortDirection === 'asc' ? ' ▲' : ' ▼'
}

function toggleDetail(id: number) {
  expandedStrainId.value = expandedStrainId.value === id ? null : id
}

function openEdit(strain: Strain) {
  editTarget.value = strain
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

onMounted(async () => {
  // The vocabulary drives the filter dropdowns and the modal's chips, so both
  // land before the first render that needs them.
  await Promise.all([store.fetchAll(), store.fetchVocabulary()])
})

async function handleCreate(data: StrainCreate) {
  try {
    await store.create(data)
    notify(`${data.name} | added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Add failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: StrainUpdate) {
  const name = store.items.find((s) => s.id === id)?.name ?? 'Strain'
  try {
    await store.update(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await store.remove(id)
    notify(`${name} | deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Delete failed: ${detail}`, 'error')
  }
}
</script>
