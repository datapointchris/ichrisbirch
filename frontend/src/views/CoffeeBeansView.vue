<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column grid--tight">
      <div class="coffee-beans__header">
        <h1 class="coffee-beans__title">Coffee Beans</h1>
        <button
          class="button"
          data-testid="add-bean-button"
          @click="showAddModal = true"
        >
          <span class="button__text">Add Bean</span>
        </button>
      </div>
    </div>

    <div class="grid grid--one-column grid--tight">
      <div class="coffee-beans__filters">
        <NeuSelect
          :model-value="beansStore.roastLevelFilter"
          :options="roastFilterOptions"
          data-testid="bean-roast-filter"
          @update:model-value="beansStore.setRoastLevelFilter($event)"
        />
        <NeuSelect
          :model-value="beansStore.brewMethodFilter"
          :options="brewFilterOptions"
          data-testid="bean-brew-filter"
          @update:model-value="beansStore.setBrewMethodFilter($event)"
        />
        <NeuSelect
          :model-value="beansStore.sortField"
          :options="sortOptions"
          data-testid="bean-sort-select"
          @update:model-value="beansStore.setSort($event)"
        />
      </div>
    </div>

    <div class="grid grid--three-columns">
      <div
        v-if="beansStore.loading"
        class="coffee-beans__empty"
      >
        Loading...
      </div>
      <div
        v-else-if="beansStore.filteredItems.length === 0"
        class="coffee-beans__empty"
      >
        No beans yet. Add one!
      </div>
      <template v-else>
        <div
          v-for="bean in beansStore.filteredItems"
          :key="bean.id"
          class="coffee-beans__card"
          data-testid="bean-card"
        >
          <div class="coffee-beans__card-header">
            <div>
              <h3 class="coffee-beans__card-name">{{ bean.name }}</h3>
              <span
                v-if="bean.roaster"
                class="coffee-beans__card-roaster"
                >{{ bean.roaster }}</span
              >
            </div>
            <div class="coffee-shops__card-rating">
              <span
                v-for="n in 5"
                :key="n"
                class="coffee-star"
                :class="{ 'coffee-star--filled': n <= Math.round(bean.rating ?? 0) }"
              ></span>
            </div>
          </div>

          <div class="coffee-beans__card-meta">
            <span
              v-if="bean.origin"
              class="coffee-beans__card-badge"
              >{{ bean.origin }}</span
            >
            <span
              v-if="bean.process"
              class="coffee-beans__card-badge"
              >{{ bean.process }}</span
            >
            <span
              v-if="bean.roast_level"
              class="coffee-beans__card-roast-badge"
              >{{ bean.roast_level }}</span
            >
            <span
              v-if="bean.brew_method"
              class="coffee-beans__card-badge"
              >{{ bean.brew_method }}</span
            >
          </div>

          <div
            v-if="bean.flavor_notes"
            class="coffee-beans__flavor-notes"
          >
            <span
              v-for="note in bean.flavor_notes
                .split(',')
                .map((n) => n.trim())
                .filter(Boolean)"
              :key="note"
              class="coffee-beans__flavor-pill"
              >{{ note }}</span
            >
          </div>

          <p
            v-if="bean.notes"
            class="coffee-beans__card-notes"
          >
            {{ bean.notes }}
          </p>

          <p
            v-if="bean.review"
            class="coffee-beans__card-review"
          >
            <i class="fa-solid fa-quote-left coffee-beans__card-review-icon"></i>
            {{ bean.review }}
          </p>

          <div class="coffee-beans__card-footer">
            <span
              v-if="bean.price"
              class="coffee-beans__card-price"
              >${{ bean.price.toFixed(2) }}</span
            >
            <span
              v-if="shopName(bean)"
              class="coffee-beans__card-source"
              >From: {{ shopName(bean) }}</span
            >
          </div>

          <div class="coffee-beans__card-actions">
            <button
              class="button-icon"
              data-testid="bean-edit-button"
              title="Edit"
              @click="openEdit(bean)"
            >
              <i class="fa-solid fa-pen"></i>
            </button>
            <button
              class="button-icon danger"
              data-testid="bean-delete-button"
              title="Delete"
              @click="handleDelete(bean.id, bean.name)"
            >
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </div>
      </template>
    </div>

    <AddEditCoffeeBeanModal
      :visible="showAddModal || !!editBean"
      :edit-data="editBean"
      @close="handleModalClose"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { CoffeeBean, CoffeeBeanCreate, CoffeeBeanUpdate } from '@/api/client'
import { useCoffeeBeansStore, ROAST_LEVELS, BREW_METHODS } from '@/stores/coffeeBeans'
import { useCoffeeShopsStore } from '@/stores/coffeeShops'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import NeuSelect from '@/components/NeuSelect.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { COFFEE_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = COFFEE_SUBNAV
import AddEditCoffeeBeanModal from '@/components/coffee/AddEditCoffeeBeanModal.vue'

const beansStore = useCoffeeBeansStore()
const shopsStore = useCoffeeShopsStore()
const { show: notify } = useNotifications()

const showAddModal = ref(false)
const editBean = ref<CoffeeBean | null>(null)

const roastFilterOptions = computed(() => [
  { value: 'all', label: 'All Roasts' },
  ...ROAST_LEVELS.map((r) => ({ value: r, label: r.charAt(0).toUpperCase() + r.slice(1) })),
])

const brewFilterOptions = computed(() => [
  { value: 'all', label: 'All Brew Methods' },
  ...BREW_METHODS.map((m) => ({ value: m, label: m.charAt(0).toUpperCase() + m.slice(1) })),
])

const sortOptions = [
  { value: 'name', label: 'Sort: Name' },
  { value: 'roaster', label: 'Sort: Roaster' },
  { value: 'origin', label: 'Sort: Origin' },
  { value: 'rating', label: 'Sort: Rating' },
  { value: 'price', label: 'Sort: Price' },
  { value: 'purchase_date', label: 'Sort: Date' },
]

onMounted(async () => {
  await Promise.all([beansStore.fetchAll(), shopsStore.fetchAll()])
})

function shopName(bean: CoffeeBean): string | null {
  if (bean.coffee_shop_id != null) {
    return shopsStore.items.find((s) => s.id === bean.coffee_shop_id)?.name ?? null
  }
  return bean.purchase_source ?? null
}

function openEdit(bean: CoffeeBean) {
  editBean.value = bean
}

function handleModalClose() {
  showAddModal.value = false
  editBean.value = null
}

async function handleCreate(data: CoffeeBeanCreate) {
  try {
    await beansStore.create(data)
    notify(`${data.name} | added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Add failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: CoffeeBeanUpdate) {
  try {
    await beansStore.update(id, data)
    notify('Bean updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await beansStore.remove(id)
    notify(`${name} | deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Delete failed: ${detail}`, 'error')
  }
}
</script>
