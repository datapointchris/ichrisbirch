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
        <h2>{{ editData ? 'Edit Event' : 'Add Event' }}</h2>

        <div class="add-edit-modal__form-item">
          <label for="event-name">Name</label>
          <input
            id="event-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="event-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="event-date">Date and Time</label>
            <input
              id="event-date"
              v-model="form.date"
              data-testid="event-date-input"
              type="datetime-local"
              class="textbox"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="event-venue">Venue</label>
            <input
              id="event-venue"
              v-model="form.venue"
              data-testid="event-venue-input"
              type="text"
              class="textbox"
              required
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="event-url">URL</label>
          <input
            id="event-url"
            v-model="form.url"
            data-testid="event-url-input"
            type="text"
            class="textbox"
          />
        </div>

        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="event-cost">Cost</label>
            <input
              id="event-cost"
              v-model="form.cost"
              data-testid="event-cost-input"
              type="number"
              class="textbox add-edit-modal__number-input"
              step="any"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="event-attending">Attending</label>
            <input
              id="event-attending"
              v-model="form.attending"
              data-testid="event-attending-input"
              type="checkbox"
            />
          </div>
        </div>

        <div class="add-edit-modal__form-item">
          <label for="event-notes">Notes</label>
          <textarea
            id="event-notes"
            v-model="form.notes"
            data-testid="event-notes-input"
            rows="3"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="event-submit-button"
            class="button"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Event</span>
          </button>
          <button
            type="button"
            data-testid="event-cancel-button"
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
import type { Event, EventCreate, EventUpdate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'

const props = defineProps<{
  visible: boolean
  editData?: Event | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: EventCreate]
  update: [id: number, data: EventUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  date: '',
  venue: '',
  url: '',
  cost: 0,
  attending: false,
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.name = props.editData.name
      form.date = props.editData.date
      form.venue = props.editData.venue
      form.url = props.editData.url ?? ''
      form.cost = props.editData.cost
      form.attending = props.editData.attending
      form.notes = props.editData.notes ?? ''
    }
  }
)

function resetForm() {
  form.name = ''
  form.date = ''
  form.venue = ''
  form.url = ''
  form.cost = 0
  form.attending = false
  form.notes = ''
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function handleSubmit(handleSuccess: () => void) {
  if (!form.name.trim() || !form.date || !form.venue.trim()) return
  const data = {
    name: form.name.trim(),
    date: form.date,
    venue: form.venue.trim(),
    url: form.url.trim() || undefined,
    cost: Number(form.cost),
    attending: form.attending,
    notes: form.notes.trim() || undefined,
  }
  if (props.editData) {
    emit('update', props.editData.id, data)
  } else {
    emit('create', data)
  }
  handleSuccess()
}
</script>
