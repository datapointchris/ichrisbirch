<template>
  <Teleport to="body">
    <div
      id="add-task-background-overlay"
      :class="{ visible: visible && !closeMode, closing: closeMode === 'cancel', 'closing-success': closeMode === 'success' }"
      @click="handleClose"
    ></div>
    <div
      id="add-task-window"
      :class="{
        visible: visible && !closeMode,
        closing: closeMode === 'cancel',
        'closing-success': closeMode === 'success',
      }"
      @animationend="onAnimationEnd"
    >
      <form
        class="add-task-form"
        @submit.prevent="handleSubmit"
      >
        <h2>Add New Task</h2>

        <div class="add-task-form__item">
          <label for="add-task-name">Name</label>
          <input
            id="add-task-name"
            ref="nameInput"
            v-model="form.name"
            type="text"
            size="50"
            class="textbox"
          />
        </div>

        <div class="add-task-form__item">
          <label>Category</label>
          <div class="add-task-categories">
            <template
              v-for="cat in categories"
              :key="cat"
            >
              <input
                :id="'cat-' + cat"
                v-model="form.category"
                type="radio"
                class="add-task-categories__input"
                :value="cat"
              />
              <label
                :for="'cat-' + cat"
                class="add-task-categories__tile"
              >
                {{ cat }}
              </label>
            </template>
          </div>
        </div>

        <div class="add-task-form__row">
          <div class="add-task-form__item">
            <label for="add-task-priority">Priority</label>
            <input
              id="add-task-priority"
              v-model.number="form.priority"
              type="number"
              class="textbox add-task-priority-input"
              min="1"
            />
          </div>
        </div>

        <div class="add-task-form__item">
          <label for="add-task-notes">Notes</label>
          <textarea
            id="add-task-notes"
            v-model="form.notes"
            rows="3"
            cols="50"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-task-form__buttons">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Task</span>
          </button>
          <button
            type="button"
            class="button button--danger"
            @click="handleClose"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, ref, watch, nextTick } from 'vue'
import type { TaskCategory } from '@/api/client'
import { TASK_CATEGORIES } from '@/stores/tasks'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [data: { name: string; category: TaskCategory; priority: number; notes?: string }]
}>()

const categories = TASK_CATEGORIES
const closeMode = ref<'cancel' | 'success' | null>(null)
const nameInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  category: 'Chore' as TaskCategory,
  priority: 10,
  notes: '',
})

watch(
  () => props.visible,
  (val) => {
    if (val) {
      nextTick(() => nameInput.value?.focus())
    }
  }
)

function handleClose() {
  if (!props.visible || closeMode.value) return
  closeMode.value = 'cancel'
}

function onAnimationEnd(event: AnimationEvent) {
  if (event.animationName === 'window-cancel-squeeze' || event.animationName === 'window-success-squeeze') {
    form.name = ''
    form.notes = ''
    closeMode.value = null
    emit('close')
  }
}

function handleSubmit() {
  if (!form.name.trim()) return
  emit('create', {
    name: form.name.trim(),
    category: form.category,
    priority: form.priority,
    notes: form.notes.trim() || undefined,
  })
  closeMode.value = 'success'
}
</script>
