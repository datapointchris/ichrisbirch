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
        <h2>{{ editData ? 'Edit Item' : 'Add Item' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="item-box">Box</label>
          <select
            id="item-box"
            v-model="form.box_id"
            data-testid="item-box-input"
            class="textbox"
            required
          >
            <option
              value=""
              disabled
            >
              Select a box
            </option>
            <option
              v-for="box in boxes"
              :key="box.id"
              :value="box.id"
            >
              Box {{ box.number }}: {{ box.name }} ({{ box.size }})
            </option>
          </select>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="item-name">Name</label>
          <input
            id="item-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="item-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-item">
          <label>Attributes</label>
          <div class="packed-box-item__details">
            <span>
              <input
                id="item-essential"
                v-model="form.essential"
                data-testid="item-essential-input"
                type="checkbox"
              />
              <label
                for="item-essential"
                class="packed-box-item__details--essential"
                >Essential</label
              >
            </span>
            <span>
              <input
                id="item-warm"
                v-model="form.warm"
                data-testid="item-warm-input"
                type="checkbox"
              />
              <label
                for="item-warm"
                class="packed-box-item__details--warm"
                >Warm</label
              >
            </span>
            <span>
              <input
                id="item-liquid"
                v-model="form.liquid"
                data-testid="item-liquid-input"
                type="checkbox"
              />
              <label
                for="item-liquid"
                class="packed-box-item__details--liquid"
                >Liquid</label
              >
            </span>
          </div>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="item-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Item</span>
          </button>
          <button
            type="button"
            data-testid="item-cancel-button"
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
import type { Box, BoxItemCreate, BoxItemUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  boxes: Box[]
  preselectedBoxId?: number
  editData?: {
    id: number
    box_id: number
    name: string
    essential: boolean
    warm: boolean
    liquid: boolean
  } | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: BoxItemCreate]
  update: [id: number, data: BoxItemUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  box_id: '' as string | number,
  name: '',
  essential: false,
  warm: false,
  liquid: false,
})

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.editData) {
        form.box_id = props.editData.box_id
        form.name = props.editData.name
        form.essential = props.editData.essential
        form.warm = props.editData.warm
        form.liquid = props.editData.liquid
      } else if (props.preselectedBoxId) {
        form.box_id = props.preselectedBoxId
      }
    }
  }
)

function resetForm() {
  form.box_id = ''
  form.name = ''
  form.essential = false
  form.warm = false
  form.liquid = false
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.box_id) return
  if (props.editData) {
    emit('update', props.editData.id, {
      box_id: Number(form.box_id),
      name: form.name.trim(),
      essential: form.essential,
      warm: form.warm,
      liquid: form.liquid,
    })
  } else {
    emit('create', {
      box_id: Number(form.box_id),
      name: form.name.trim(),
      essential: form.essential,
      warm: form.warm,
      liquid: form.liquid,
    })
  }
  handleSuccess()
}
</script>
