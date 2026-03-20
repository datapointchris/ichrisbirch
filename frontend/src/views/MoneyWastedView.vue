<template>
  <div>
    <h1 class="money-wasted--total">
      Total Money Wasted:
      <span class="money-wasted--total-amount">{{ formatCurrency(store.totalWasted) }}</span>
    </h1>

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
            <span>Delete</span>
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
            class="money-wasted__row"
          >
            <span class="money-wasted__item-name">{{ entry.item }}</span>
            <span>{{ formatCurrency(entry.amount) }}</span>
            <span>{{ entry.date_purchased ? formatDate(entry.date_purchased) : '' }}</span>
            <span>{{ formatDate(entry.date_wasted) }}</span>
            <span
              class="money-wasted__notes"
              :title="entry.notes || ''"
              >{{ entry.notes || '' }}</span
            >
            <span>
              <button
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

    <div class="add-item-wrapper">
      <h2>Add New Money Wasted:</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleAdd"
      >
        <div class="add-item-form__item">
          <label for="item">Item:</label>
          <input
            id="item"
            v-model="form.item"
            type="text"
            size="30"
            class="textbox"
            name="item"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="amount">Amount:</label>
          <input
            id="amount"
            v-model="form.amount"
            type="number"
            step="0.01"
            min="0"
            class="textbox"
            name="amount"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="date_purchased">Date Purchased:</label>
          <DatePicker
            :model-value="form.date_purchased"
            @update:model-value="form.date_purchased = $event"
          />
        </div>
        <div class="add-item-form__item">
          <label for="date_wasted">Date Wasted:</label>
          <DatePicker
            :model-value="form.date_wasted"
            @update:model-value="form.date_wasted = $event"
          />
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <label for="notes">Notes:</label>
          <input
            id="notes"
            v-model="form.notes"
            type="text"
            size="40"
            class="textbox"
            name="notes"
          />
        </div>
        <div class="add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Money Wasted</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useMoneyWastedStore } from '@/stores/moneyWasted'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import DatePicker from '@/components/DatePicker.vue'

const store = useMoneyWastedStore()
const { show: notify } = useNotifications()

const form = reactive({
  item: '',
  amount: '',
  date_purchased: '',
  date_wasted: '',
  notes: '',
})

onMounted(() => {
  store.fetchAll()
})

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

async function handleAdd() {
  if (!form.item.trim() || !form.date_wasted) return
  try {
    await store.create({
      item: form.item.trim(),
      amount: Number(form.amount),
      date_purchased: form.date_purchased || undefined,
      date_wasted: form.date_wasted,
      notes: form.notes.trim() || undefined,
    })
    notify('Money wasted entry added', 'success')
    form.item = ''
    form.amount = ''
    form.date_purchased = ''
    form.date_wasted = ''
    form.notes = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add entry: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  try {
    await store.remove(id)
    notify('Entry deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete entry: ${detail}`, 'error')
  }
}
</script>
