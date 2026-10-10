<template>
  <div
    class="shopping-section__header"
    data-testid="shopping-section-header"
  >
    <button
      type="button"
      class="shopping-section__toggle"
      data-testid="shopping-section-toggle"
      :aria-expanded="!collapsed"
      :aria-label="collapsed ? `Expand ${title}` : `Collapse ${title}`"
      @click="emit('toggle')"
    >
      <i
        class="fa-solid"
        :class="collapsed ? 'fa-caret-right' : 'fa-caret-down'"
      ></i>
    </button>
    <input
      v-if="editing"
      ref="nameInput"
      v-model="draft"
      type="text"
      class="textbox shopping-section__name-input"
      data-testid="shopping-section-name-input"
      aria-label="Section name"
      @keydown.enter.prevent="save"
      @keydown.esc.prevent="cancel"
      @blur="save"
    />
    <button
      v-else-if="section"
      type="button"
      class="shopping-section__name"
      data-testid="shopping-section-name"
      @click="startRename"
    >
      {{ section.name }}
    </button>
    <span
      v-else
      class="shopping-section__name shopping-section__name--unsorted"
      data-testid="shopping-section-name"
    >
      Unsorted
    </span>
    <span
      class="shopping-section__count"
      data-testid="shopping-section-count"
    >
      {{ count }}
    </span>
    <template v-if="section">
      <button
        type="button"
        class="shopping-section__delete"
        :class="{ 'shopping-section__delete--confirming': confirmingDelete }"
        data-testid="shopping-section-delete"
        :aria-label="confirmingDelete ? `Confirm deleting ${section.name}` : `Delete ${section.name}`"
        @click="onDelete"
      >
        <span v-if="confirmingDelete">Delete?</span>
        <i
          v-else
          class="fa-solid fa-trash"
        ></i>
      </button>
      <span
        class="shopping-section__grip"
        data-testid="shopping-section-grip"
        aria-hidden="true"
      >
        <i class="fa-solid fa-grip-vertical"></i>
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import type { ShoppingSection } from '@/api/client'

const props = defineProps<{
  section: ShoppingSection | null
  count: number
  collapsed: boolean
}>()

const emit = defineEmits<{
  toggle: []
  rename: [name: string]
  delete: []
}>()

// The first tap on delete arms it, and it disarms itself if the second never comes.
const DELETE_ARMED_MS = 3000

const title = computed(() => props.section?.name ?? 'Unsorted')
const editing = ref(false)
const draft = ref('')
const nameInput = ref<HTMLInputElement | null>(null)
const confirmingDelete = ref(false)
let disarmTimer: ReturnType<typeof setTimeout> | null = null

async function startRename() {
  if (!props.section) return
  draft.value = props.section.name
  editing.value = true
  await nextTick()
  nameInput.value?.focus()
  nameInput.value?.select()
}

function save() {
  if (!editing.value) return
  editing.value = false
  const name = draft.value.trim()
  if (name && name !== props.section?.name) emit('rename', name)
}

function cancel() {
  editing.value = false
}

function disarm() {
  confirmingDelete.value = false
  if (disarmTimer) clearTimeout(disarmTimer)
  disarmTimer = null
}

function onDelete() {
  if (confirmingDelete.value) {
    disarm()
    emit('delete')
    return
  }
  confirmingDelete.value = true
  disarmTimer = setTimeout(disarm, DELETE_ARMED_MS)
}

onBeforeUnmount(disarm)
</script>
