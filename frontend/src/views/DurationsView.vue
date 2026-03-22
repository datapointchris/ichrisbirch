<template>
  <div>
    <!-- Compare bar -->
    <Transition name="slide-down">
      <div
        v-if="compareMode && selectedForCompare.length > 0"
        class="duration-compare"
      >
        <div class="duration-compare__chips">
          <span
            v-for="(item, idx) in selectedForCompare"
            :key="idx"
            class="duration-compare__chip"
          >
            {{ item.label }} ({{ formatDate(item.date, 'shortDate') }})
            <button
              class="duration-compare__chip-remove"
              @click="removeFromCompare(idx)"
            >
              &times;
            </button>
          </span>
        </div>
        <div
          v-if="selectedForCompare.length >= 2"
          class="duration-compare__results"
        >
          <div
            v-for="(pair, idx) in comparePairs"
            :key="idx"
            class="duration-compare__pair"
          >
            {{ pair.label1 }} &harr; {{ pair.label2 }}: <strong>{{ pair.elapsed }}</strong>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Controls bar -->
    <div class="duration-controls">
      <div class="duration-controls__filters">
        <NeuSelect
          :model-value="filterStatus"
          :options="filterOptions"
          @update:model-value="filterStatus = $event"
        />
        <NeuSelect
          :model-value="sortBy"
          :options="sortOptions"
          @update:model-value="sortBy = $event"
        />
      </div>
      <button
        class="button"
        @click="compareMode = !compareMode"
      >
        <span class="button__text">{{ compareMode ? 'Exit Compare' : 'Compare Dates' }}</span>
      </button>
    </div>

    <div class="grid grid--one-column">
      <div
        v-if="store.loading"
        class="grid__item"
      >
        <h2>Loading...</h2>
      </div>
      <div
        v-else-if="displayedDurations.length === 0"
        class="grid__item"
      >
        <h2>No Durations</h2>
      </div>
      <template v-else>
        <div
          v-for="duration in displayedDurations"
          :key="duration.id"
          data-testid="duration-item"
          class="grid__item duration-card"
          :style="cardStyle(duration)"
        >
          <!-- Card header -->
          <div class="duration-card__header">
            <h2 :class="{ 'duration-card__title--completed': !!duration.end_date }">
              {{ duration.name }}
            </h2>
            <span
              class="duration-card__elapsed"
              :style="elapsedStyle(duration)"
            >
              {{ elapsedText(duration) }}
            </span>
            <span class="duration-card__dates">
              {{ formatDate(duration.start_date, 'shortDate') }}
              <template v-if="duration.end_date"> &mdash; {{ formatDate(duration.end_date, 'shortDate') }}</template>
              <template v-else> &mdash; ongoing</template>
            </span>
            <p
              v-if="duration.notes"
              class="duration-card__notes"
            >
              {{ duration.notes }}
            </p>
          </div>

          <!-- Notes toggle — only expandable when notes exist -->
          <div
            v-if="duration.duration_notes.length > 0"
            class="duration-card__notes-toggle duration-card__notes-toggle--has-notes"
            @click="toggleExpand(duration.id)"
          >
            <i
              class="fa-solid fa-chevron-right duration-card__notes-chevron"
              :class="{ 'duration-card__notes-chevron--open': expandedIds.has(duration.id) }"
            ></i>
            <span>Notes ({{ duration.duration_notes.length }})</span>
          </div>
          <div
            v-else
            class="duration-card__notes-toggle duration-card__notes-toggle--empty"
          >
            <span>No notes</span>
          </div>

          <!-- Expanded notes list -->
          <Transition name="expand">
            <div
              v-if="expandedIds.has(duration.id) && duration.duration_notes.length > 0"
              class="duration-card__body"
            >
              <div class="duration-notes">
                <div
                  v-for="note in duration.duration_notes"
                  :key="note.id"
                  class="duration-notes__item"
                >
                  <span class="duration-notes__date">{{ formatDate(note.date, 'shortDate') }}</span>
                  <span class="duration-notes__from-start">{{ timeFromStart(duration.start_date, note.date) }}</span>
                  <span class="duration-notes__content">{{ note.content }}</span>
                  <button
                    class="duration-notes__delete"
                    @click="handleDeleteNote(duration.id, note.id)"
                  >
                    <i class="fa-solid fa-xmark"></i>
                  </button>
                </div>
              </div>
            </div>
          </Transition>

          <!-- Compare checkboxes -->
          <div
            v-if="compareMode"
            class="duration-card__compare"
          >
            <label class="duration-card__compare-item">
              <input
                type="checkbox"
                :checked="isSelected(duration.name + ' (start)', duration.start_date)"
                @change="toggleCompareItem(duration.name + ' (start)', duration.start_date)"
              />
              Start date
            </label>
            <label
              v-if="duration.end_date"
              class="duration-card__compare-item"
            >
              <input
                type="checkbox"
                :checked="isSelected(duration.name + ' (end)', duration.end_date)"
                @change="toggleCompareItem(duration.name + ' (end)', duration.end_date)"
              />
              End date
            </label>
            <label
              v-for="note in duration.duration_notes"
              :key="note.id"
              class="duration-card__compare-item"
            >
              <input
                type="checkbox"
                :checked="isSelected(duration.name + ': ' + note.content.slice(0, 30), note.date)"
                @change="toggleCompareItem(duration.name + ': ' + note.content.slice(0, 30), note.date)"
              />
              {{ note.content.slice(0, 40) }}
            </label>
          </div>

          <!-- Add note form (always visible) -->
          <div class="duration-card__add-note">
            <DatePicker
              :model-value="noteForm[duration.id]!.date"
              placeholder="Date"
              @update:model-value="noteForm[duration.id]!.date = $event"
            />
            <input
              v-model="noteForm[duration.id]!.content"
              type="text"
              class="textbox"
              placeholder="Note content"
              @keyup.enter="handleAddNote(duration.id)"
            />
            <button
              class="button button--small"
              @click="handleAddNote(duration.id)"
            >
              <span class="button__text">Add Note</span>
            </button>
          </div>

          <!-- End Duration (only for ongoing) -->
          <div
            v-if="!duration.end_date"
            class="duration-card__end-form"
          >
            <DatePicker
              :model-value="endDateForm[duration.id] ?? ''"
              @update:model-value="endDateForm[duration.id] = $event"
            />
            <button
              class="button button--small"
              @click="handleEndDuration(duration.id)"
            >
              <span class="button__text">End Duration</span>
            </button>
          </div>

          <!-- Actions -->
          <div class="duration-card__actions">
            <button
              data-testid="duration-edit-button"
              class="button button--small"
              @click="openEdit(duration)"
            >
              <span class="button__text">Edit</span>
            </button>
            <button
              v-if="duration.end_date"
              data-testid="duration-reopen-button"
              class="button button--small"
              @click="handleReopenDuration(duration.id)"
            >
              <span class="button__text">Reopen Duration</span>
            </button>
            <button
              data-testid="duration-delete-button"
              class="button button--danger button--small"
              @click="handleDelete(duration.id)"
            >
              <span class="button__text button__text--danger">Delete</span>
            </button>
          </div>
        </div>
      </template>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="duration-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Duration</span>
      </button>
    </div>

    <AddEditDurationModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDurationsStore } from '@/stores/durations'
import { useNotifications } from '@/composables/useNotifications'
import { computeElapsedTime, computeTimeBetween } from '@/composables/useElapsedTime'
import { formatDate } from '@/composables/formatDate'
import NeuSelect from '@/components/NeuSelect.vue'
import { ApiError } from '@/api/errors'
import type { Duration, DurationCreate, DurationUpdate } from '@/api/client'
import DatePicker from '@/components/DatePicker.vue'
import AddEditDurationModal from '@/components/durations/AddEditDurationModal.vue'

const store = useDurationsStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<{
  id: number
  name: string
  start_date: string
  end_date?: string
  notes?: string
  color?: string
} | null>(null)

// Per-duration note form state
const noteForm = ref<Record<number, { date: string; content: string }>>({})

// Per-duration end date form state
const endDateForm = ref<Record<number, string>>({})

// Initialize note forms when durations change
watch(
  () => store.durations,
  (durations) => {
    for (const d of durations) {
      if (!noteForm.value[d.id]) {
        noteForm.value[d.id] = { date: '', content: '' }
      }
      if (!(d.id in endDateForm.value)) {
        endDateForm.value[d.id] = ''
      }
    }
  },
  { immediate: true, deep: true }
)

const expandedIds = ref(new Set<number>())
const compareMode = ref(false)
const selectedForCompare = ref<Array<{ label: string; date: string }>>([])
const filterStatus = ref<'all' | 'ongoing' | 'completed'>('all')
const filterOptions = [
  { value: 'all' as const, label: 'All' },
  { value: 'ongoing' as const, label: 'Ongoing' },
  { value: 'completed' as const, label: 'Completed' },
]
const sortBy = ref<'start_asc' | 'start_desc' | 'end_asc' | 'end_desc' | 'longest' | 'shortest'>('start_asc')
const sortOptions = [
  { value: 'start_asc' as const, label: 'Start Date (oldest)' },
  { value: 'start_desc' as const, label: 'Start Date (newest)' },
  { value: 'end_asc' as const, label: 'End Date (oldest)' },
  { value: 'end_desc' as const, label: 'End Date (newest)' },
  { value: 'longest' as const, label: 'Longest' },
  { value: 'shortest' as const, label: 'Shortest' },
]

function getDurationDays(d: Duration): number {
  return computeElapsedTime(d.start_date, d.end_date ?? undefined).totalDays
}

const displayedDurations = computed(() => {
  let list = [...store.durations]

  // Filter
  if (filterStatus.value === 'ongoing') {
    list = list.filter((d) => !d.end_date)
  } else if (filterStatus.value === 'completed') {
    list = list.filter((d) => !!d.end_date)
  }

  list.sort((a, b) => {
    switch (sortBy.value) {
      case 'start_asc':
        return a.start_date.localeCompare(b.start_date)
      case 'start_desc':
        return b.start_date.localeCompare(a.start_date)
      case 'end_asc':
        return (a.end_date ?? '9999').localeCompare(b.end_date ?? '9999')
      case 'end_desc':
        return (b.end_date ?? '0000').localeCompare(a.end_date ?? '0000')
      case 'longest':
        return getDurationDays(b) - getDurationDays(a)
      case 'shortest':
        return getDurationDays(a) - getDurationDays(b)
      default:
        return 0
    }
  })

  return list
})

const comparePairs = computed(() => {
  const pairs: Array<{ label1: string; label2: string; elapsed: string }> = []
  const items = selectedForCompare.value
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const result = computeTimeBetween(items[i]!.date, items[j]!.date)
      pairs.push({
        label1: items[i]!.label,
        label2: items[j]!.label,
        elapsed: result.text,
      })
    }
  }
  return pairs
})

onMounted(() => {
  store.fetchAll()
})

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

function elapsedText(duration: Duration): string {
  return computeElapsedTime(duration.start_date, duration.end_date ?? undefined).text
}

function timeFromStart(startDate: string, noteDate: string): string {
  return computeTimeBetween(startDate, noteDate).text
}

function cardStyle(duration: Duration) {
  if (duration.color) {
    return { borderLeftColor: duration.color }
  }
  return {}
}

function elapsedStyle(duration: Duration) {
  if (duration.color) {
    return { color: duration.color }
  }
  return {}
}

function isSelected(label: string, date: string): boolean {
  return selectedForCompare.value.some((s) => s.label === label && s.date === date)
}

function toggleCompareItem(label: string, date: string) {
  const idx = selectedForCompare.value.findIndex((s) => s.label === label && s.date === date)
  if (idx !== -1) {
    selectedForCompare.value.splice(idx, 1)
  } else if (selectedForCompare.value.length < 5) {
    selectedForCompare.value.push({ label, date })
  }
}

function removeFromCompare(idx: number) {
  selectedForCompare.value.splice(idx, 1)
}

function openEdit(duration: Duration) {
  editTarget.value = {
    id: duration.id,
    name: duration.name,
    start_date: duration.start_date,
    end_date: duration.end_date,
    notes: duration.notes,
    color: duration.color,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: DurationCreate) {
  try {
    await store.create(data)
    notify('Duration added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add duration: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: DurationUpdate) {
  try {
    await store.update(id, data)
    notify('Duration updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update duration: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  const name = store.durations.find((d) => d.id === id)?.name
  try {
    await store.remove(id)
    expandedIds.value.delete(id)
    notify(`${name} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete duration: ${detail}`, 'error')
  }
}

async function handleEndDuration(id: number) {
  const dateStr = endDateForm.value[id]
  if (!dateStr) return
  const name = store.durations.find((d) => d.id === id)?.name
  try {
    await store.update(id, { end_date: dateStr })
    endDateForm.value[id] = ''
    notify(`${name} ended`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to end duration: ${detail}`, 'error')
  }
}

async function handleReopenDuration(id: number) {
  const name = store.durations.find((d) => d.id === id)?.name
  try {
    await store.update(id, { end_date: null })
    notify(`${name} reopened`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to reopen duration: ${detail}`, 'error')
  }
}

async function handleAddNote(durationId: number) {
  const nf = noteForm.value[durationId]
  if (!nf || !nf.date || !nf.content.trim()) return
  try {
    await store.addNote(durationId, { date: nf.date, content: nf.content.trim() })
    nf.date = ''
    nf.content = ''
    const name = store.durations.find((d) => d.id === durationId)?.name
    notify(`Note added to ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add note: ${detail}`, 'error')
  }
}

async function handleDeleteNote(durationId: number, noteId: number) {
  try {
    await store.removeNote(durationId, noteId)
    const name = store.durations.find((d) => d.id === durationId)?.name
    notify(`Note removed from ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete note: ${detail}`, 'error')
  }
}
</script>
