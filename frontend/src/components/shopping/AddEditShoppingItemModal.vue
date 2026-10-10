<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="nameInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        data-testid="add-edit-modal"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Item' : 'Add Item' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="shopping-item-name">Name</label>
          <input
            id="shopping-item-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="shopping-item-name-input"
            type="text"
            class="textbox"
            autocomplete="off"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label for="shopping-item-note">Note</label>
          <input
            id="shopping-item-note"
            v-model="form.note"
            data-testid="shopping-item-note-input"
            type="text"
            class="textbox"
            placeholder="2 dozen, the blue one, a link"
            autocomplete="off"
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label>Section</label>
          <NeuSelect
            :model-value="form.section"
            :options="sectionOptions"
            data-testid="shopping-item-section-input"
            @update:model-value="chooseSection"
          />
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="shopping-item-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Save' : 'Add' }}</span>
          </button>
          <button
            type="button"
            data-testid="shopping-item-cancel-button"
            class="button button--danger"
            @click="handleClose()"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>

        <div
          v-if="editData"
          class="add-edit-modal__form-buttons"
        >
          <button
            v-if="editData.is_needed"
            type="button"
            data-testid="shopping-item-remove-button"
            class="button"
            @click="handleRemove(handleSuccess)"
          >
            <span class="button__text">Off the list</span>
          </button>
          <button
            type="button"
            data-testid="shopping-item-delete-button"
            class="button button--danger"
            @click="handleDelete(handleSuccess)"
          >
            <span class="button__text button__text--danger">{{ deleteArmed ? 'Forget it?' : 'Forget item' }}</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate, ShoppingSection } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import { UNSORTED_KEY } from '@/stores/shopping'

const props = defineProps<{
  visible: boolean
  sections: ShoppingSection[]
  catalog: ShoppingItem[]
  editData?: ShoppingItem | null
  initialName?: string
}>()

const emit = defineEmits<{
  close: []
  create: [data: ShoppingItemCreate]
  update: [id: string, data: ShoppingItemUpdate]
  remove: [id: string]
  delete: [id: string]
}>()

const nameInput = ref<HTMLInputElement | null>(null)
const deleteArmed = ref(false)
// Adding a known name preselects the section it was last in, until a section is chosen by hand.
const sectionChosen = ref(false)

const form = reactive({
  name: '',
  note: '',
  section: UNSORTED_KEY as string,
})

const sectionOptions = computed(() => [
  { value: UNSORTED_KEY, label: 'Unsorted' },
  ...[...props.sections].sort((a, b) => a.rank - b.rank).map((section) => ({ value: section.id, label: section.name })),
])

function rememberedSection(name: string): string {
  const folded = name.trim().toLowerCase()
  const known = props.catalog.find((item) => item.name.toLowerCase() === folded)
  return known?.section_id ?? UNSORTED_KEY
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) return
    deleteArmed.value = false
    sectionChosen.value = false
    if (props.editData) {
      form.name = props.editData.name
      form.note = props.editData.note ?? ''
      form.section = props.editData.section_id ?? UNSORTED_KEY
    } else {
      form.name = props.initialName ?? ''
      form.note = ''
      form.section = rememberedSection(form.name)
    }
  }
)

watch(
  () => form.name,
  (name) => {
    if (!props.editData && !sectionChosen.value) form.section = rememberedSection(name)
  }
)

function chooseSection(key: string) {
  form.section = key
  sectionChosen.value = true
}

function sectionRef(): string | null {
  return form.section === UNSORTED_KEY ? null : form.section
}

function resetForm() {
  form.name = ''
  form.note = ''
  form.section = UNSORTED_KEY
  deleteArmed.value = false
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  const name = form.name.trim()
  if (!name) return
  if (props.editData) {
    emit('update', props.editData.id, { name, note: form.note.trim() || null, section: sectionRef() })
  } else {
    emit('create', { name, note: form.note.trim() || undefined, section: sectionRef() })
  }
  handleSuccess()
}

function handleRemove(handleSuccess: () => void) {
  if (!props.editData) return
  emit('remove', props.editData.id)
  handleSuccess()
}

function handleDelete(handleSuccess: () => void) {
  if (!props.editData) return
  if (!deleteArmed.value) {
    deleteArmed.value = true
    return
  }
  emit('delete', props.editData.id)
  handleSuccess()
}
</script>
