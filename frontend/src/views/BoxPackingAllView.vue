<template>
  <div>
    <BoxPackingSubnav active="all" />

    <div class="box-listing-sort">
      <select
        v-model="store.sortField1"
        class="button"
      >
        <option
          v-for="opt in SORT_OPTIONS"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
      <select
        v-model="store.sortField2"
        class="button"
      >
        <option value="">None</option>
        <option
          v-for="opt in SORT_OPTIONS"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
      <button
        class="button"
        :class="{ 'button--pressed': store.viewMode === 'block' }"
        @click="store.setViewMode('block')"
      >
        <i class="fa-solid fa-th-large"></i>
      </button>
      <button
        class="button"
        :class="{ 'button--pressed': store.viewMode === 'compact' }"
        @click="store.setViewMode('compact')"
      >
        <i class="fa-solid fa-list"></i>
      </button>
    </div>

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Loading...</h2>
      </div>
    </div>

    <div
      v-else-if="store.sortedBoxes.length === 0"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>No Boxes</h2>
      </div>
    </div>

    <!-- Block View -->
    <div
      v-else-if="store.viewMode === 'block'"
      class="grid grid--one-column"
    >
      <div
        v-for="box in store.sortedBoxes"
        :key="box.id"
        class="grid__item"
      >
        <h2 class="packed-box__title">
          <RouterLink
            :to="`/box-packing/box/${box.id}`"
            class="packed-box__link"
          >
            Box {{ box.number }}: {{ box.name }}
          </RouterLink>
        </h2>
        <h3>Size: {{ box.size }}</h3>
        <h4>{{ box.items.length }} Item{{ box.items.length !== 1 ? 's' : '' }}</h4>
        <div class="packed-box__details">
          <span
            v-if="box.essential"
            class="packed-box__details--essential"
            >Essential</span
          >
          <span
            v-if="box.warm"
            class="packed-box__details--warm"
            >Warm</span
          >
          <span
            v-if="box.liquid"
            class="packed-box__details--liquid"
            >Liquid</span
          >
        </div>
      </div>
    </div>

    <!-- Compact View -->
    <div v-else>
      <div
        v-for="box in store.sortedBoxes"
        :key="box.id"
        class="packed-box-compact"
      >
        <h3 class="packed-box-compact__title">
          <RouterLink
            :to="`/box-packing/box/${box.id}`"
            class="packed-box-compact__link"
          >
            Box {{ box.number }}: {{ box.name }}
          </RouterLink>
        </h3>
        <span>Size: {{ box.size }}</span>
        <span>{{ box.items.length }} Item{{ box.items.length !== 1 ? 's' : '' }}</span>
        <span
          v-if="box.essential"
          class="packed-box-compact__details--essential"
          >Essential</span
        >
        <span v-else>&nbsp;</span>
        <span
          v-if="box.warm"
          class="packed-box-compact__details--warm"
          >Warm</span
        >
        <span v-else>&nbsp;</span>
        <span
          v-if="box.liquid"
          class="packed-box-compact__details--liquid"
          >Liquid</span
        >
        <span v-else>&nbsp;</span>
        <span>&nbsp;</span>
        <span>
          <button
            class="button--hidden"
            @click="handleDelete(box.id, box.name)"
          >
            <i class="button-icon danger fa-regular fa-trash-can"></i>
          </button>
        </span>
      </div>
    </div>

    <div class="add-item-wrapper">
      <h2>Add a New Box</h2>
      <form
        class="add-item-form"
        @submit.prevent="handleAdd"
      >
        <div class="add-item-form__item">
          <label for="box_name">Name:</label>
          <input
            id="box_name"
            v-model="form.name"
            type="text"
            class="textbox"
            required
          />
        </div>
        <div class="add-item-form__item">
          <label for="box_number">Number:</label>
          <input
            id="box_number"
            v-model="form.number"
            type="number"
            class="textbox"
          />
        </div>
        <div class="add-item-form__item">
          <label for="box_size">Size:</label>
          <select
            id="box_size"
            v-model="form.size"
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
        <div class="add-item-form__item add-item-form__item--full-width">
          <div class="packed-box-item__details">
            <div>
              <input
                id="essential"
                v-model="form.essential"
                type="checkbox"
              />
              <label
                for="essential"
                class="packed-box-item__details--essential"
                >Essential</label
              >
            </div>
            <div>
              <input
                id="warm"
                v-model="form.warm"
                type="checkbox"
              />
              <label
                for="warm"
                class="packed-box-item__details--warm"
                >Warm</label
              >
            </div>
            <div>
              <input
                id="liquid"
                v-model="form.liquid"
                type="checkbox"
              />
              <label
                for="liquid"
                class="packed-box-item__details--liquid"
                >Liquid</label
              >
            </div>
          </div>
        </div>
        <div class="add-item-form__item add-item-form__item--full-width">
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Add Box</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useBoxPackingStore, BOX_SIZES, SORT_OPTIONS } from '@/stores/boxPacking'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import BoxPackingSubnav from '@/components/BoxPackingSubnav.vue'
import type { BoxSize } from '@/api/client'

const store = useBoxPackingStore()
const { show: notify } = useNotifications()

const form = reactive({
  name: '',
  number: '' as string | number,
  size: 'Medium' as BoxSize,
  essential: false,
  warm: false,
  liquid: false,
})

onMounted(() => {
  store.fetchBoxes()
})

async function handleAdd() {
  if (!form.name.trim()) return
  try {
    await store.createBox({
      name: form.name.trim(),
      number: form.number ? Number(form.number) : undefined,
      size: form.size,
      essential: form.essential,
      warm: form.warm,
      liquid: form.liquid,
    })
    notify('Box added', 'success')
    form.name = ''
    form.number = ''
    form.size = 'Medium'
    form.essential = false
    form.warm = false
    form.liquid = false
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add box: ${detail}`, 'error')
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await store.deleteBox(id)
    notify(`Box "${name}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete box: ${detail}`, 'error')
  }
}
</script>
