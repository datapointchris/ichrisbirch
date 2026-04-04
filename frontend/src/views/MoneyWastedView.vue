<template>
  <div>
    <h1 class="money-wasted--total">
      Total Money Wasted:
      <span class="money-wasted--total-amount">{{ formatCurrency(store.totalWasted) }}</span>
    </h1>

    <div class="add-item-wrapper">
      <button
        data-testid="mw-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Money Wasted</span>
      </button>
    </div>

    <div class="grid grid--one-column-full">
      <div class="grid__item money-wasted__table">
        <div
          v-if="store.loading"
          class="money-wasted__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div class="money-wasted__header">
            <span>Item</span>
            <span>Amount</span>
            <span>Purchased</span>
            <span>Wasted</span>
            <span>Notes</span>
            <span>Actions</span>
          </div>

          <div
            v-if="store.sortedItems.length === 0"
            class="money-wasted__empty"
          >
            No money wasted yet. Lucky you!
          </div>

          <div
            v-for="entry in store.sortedItems"
            :key="entry.id"
            data-testid="mw-item"
            class="money-wasted__row"
          >
            <span class="money-wasted__item-name">{{ entry.item }}</span>
            <span>{{ formatCurrency(entry.amount) }}</span>
            <span>{{ entry.date_purchased ? formatDate(entry.date_purchased, 'shortDate') : '' }}</span>
            <span>{{ formatDate(entry.date_wasted, 'shortDate') }}</span>
            <span
              class="money-wasted__notes"
              :title="entry.notes || ''"
              >{{ entry.notes || '' }}</span
            >
            <span class="money-wasted__actions">
              <button
                data-testid="mw-edit-button"
                class="button--hidden"
                @click="openEdit(entry)"
              >
                <i class="button-icon warning fa-solid fa-pen-to-square"></i>
              </button>
              <button
                data-testid="mw-delete-button"
                class="button--hidden"
                @click="handleDelete(entry.id)"
              >
                <i class="button-icon danger fa-regular fa-trash-can"></i>
              </button>
            </span>
          </div>
        </template>
      </div>
    </div>

    <AddEditMoneyWastedModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMoneyWastedStore } from '@/stores/moneyWasted'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { MoneyWasted, MoneyWastedCreate, MoneyWastedUpdate } from '@/api/client'
import AddEditMoneyWastedModal from '@/components/money-wasted/AddEditMoneyWastedModal.vue'
import { formatDate } from '@/composables/formatDate'

const store = useMoneyWastedStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<MoneyWasted | null>(null)

onMounted(() => {
  store.fetchAll()
})

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

function openEdit(entry: MoneyWasted) {
  editTarget.value = entry
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: MoneyWastedCreate) {
  try {
    await store.create(data)
    notify(`${data.item} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add entry: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: MoneyWastedUpdate) {
  const item = store.items.find((i) => i.id === id)?.item ?? 'Entry'
  try {
    await store.update(id, data)
    notify(`${item} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update entry: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  const item = store.items.find((i) => i.id === id)?.item ?? 'Entry'
  try {
    await store.remove(id)
    notify(`${item} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete entry: ${detail}`, 'error')
  }
}
</script>
