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
        <h2>{{ editData ? 'Edit Box' : 'Add Box' }}</h2>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="box-name">Name</label>
            <input
              id="box-name"
              ref="nameInput"
              v-model="form.name"
              data-testid="box-name-input"
              type="text"
              class="textbox"
              required
            />
          </div>

          <div class="add-edit-modal__form-item">
            <label for="box-number">Number</label>
            <input
              id="box-number"
              v-model="form.number"
              data-testid="box-number-input"
              type="number"
              class="textbox add-edit-modal__number-input"
              :class="{ 'textbox--error': errors.number }"
              @input="clearError('number')"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="box-size">Size</label>
          <select
            id="box-size"
            v-model="form.size"
            data-testid="box-size-input"
            class="textbox"
            required
          >
            <option
              v-for="size in BOX_SIZES"
              :key="size"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="box-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Box</span>
          </button>
          <button
            type="button"
            data-testid="box-cancel-button"
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
import { reactive, ref, watch } from 'vue'
import { useBoxPackingStore, BOX_SIZES } from '@/stores/boxPacking'
import { useFieldErrors } from '@/composables/useFieldErrors'
import type { BoxCreate, BoxUpdate, BoxSize } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const store = useBoxPackingStore()
const { errors, validate, clearError, clearAll } = useFieldErrors()

const props = defineProps<{
  visible: boolean
  editData?: {
    id: number
    name: string
    number?: number
    size: BoxSize
  } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: BoxCreate]
  update: [id: number, data: BoxUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  number: '' as string | number,
  size: 'Medium' as BoxSize,
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.number = props.editData.number ?? ''
      form.size = props.editData.size
    }
  }
)

function validateBoxNumber(): string | null {
  if (!form.number) return null
  const num = Number(form.number)
  const editingId = props.editData?.id
  const duplicate = store.boxes.find((b) => b.number === num && b.id !== editingId)
  return duplicate ? `Box number ${num} is already used by "${duplicate.name}"` : null
}

function resetForm() {
  form.name = ''
  form.number = ''
  form.size = 'Medium'
  clearAll()
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim()) return
  if (!validate({ number: validateBoxNumber() })) return
  if (props.editData) {
    emit('update', props.editData.id, {
      name: form.name.trim(),
      number: form.number ? Number(form.number) : undefined,
      size: form.size,
    })
  } else {
    emit('create', {
      name: form.name.trim(),
      number: form.number ? Number(form.number) : undefined,
      size: form.size,
      essential: false,
      warm: false,
      liquid: false,
    })
  }
  handleSuccess()
}
</script>
