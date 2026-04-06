<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column grid--tight">
      <div class="coffee-shops__header">
        <h1 class="coffee-shops__title">Coffee Shops</h1>
        <button
          class="button"
          data-testid="add-shop-button"
          @click="showAddModal = true"
        >
          <span class="button__text">Add Shop</span>
        </button>
      </div>
    </div>

    <div class="grid grid--one-column grid--tight">
      <div class="coffee-shops__filters">
        <NeuSelect
          :model-value="store.filterCity"
          :options="cityFilterOptions"
          data-testid="shop-city-filter"
          @update:model-value="store.setFilterCity($event)"
        />
        <NeuSelect
          :model-value="store.sortField"
          :options="sortOptions"
          data-testid="shop-sort-select"
          @update:model-value="store.setSort($event)"
        />
      </div>
    </div>

    <div class="grid grid--three-columns">
      <div
        v-if="store.loading"
        class="coffee-shops__empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.filteredItems.length === 0"
        class="coffee-shops__empty"
      >
        No shops yet. Add one!
      </div>
      <template v-else>
        <div
          v-for="shop in store.filteredItems"
          :key="shop.id"
          class="coffee-shops__card"
          data-testid="shop-card"
        >
          <div class="coffee-shops__card-header">
            <h3 class="coffee-shops__card-name">{{ shop.name }}</h3>
            <div class="coffee-shops__card-rating">
              <span
                v-for="n in 5"
                :key="n"
                class="coffee-star"
                :class="{ 'coffee-star--filled': n <= Math.round(shop.rating ?? 0) }"
              ></span>
            </div>
          </div>

          <div
            v-if="shop.city || shop.state || shop.country"
            class="coffee-shops__card-location"
          >
            {{ [shop.city, shop.state, shop.country].filter(Boolean).join(', ') }}
          </div>

          <p
            v-if="shop.notes"
            class="coffee-shops__card-notes"
          >
            {{ shop.notes }}
          </p>

          <p
            v-if="shop.review"
            class="coffee-shops__card-review"
          >
            <i class="fa-solid fa-quote-left coffee-shops__card-review-icon"></i>
            {{ shop.review }}
          </p>

          <div class="coffee-shops__card-actions">
            <a
              v-if="shop.google_maps_url"
              :href="shop.google_maps_url"
              target="_blank"
              rel="noopener noreferrer"
              class="button-icon"
              data-testid="shop-maps-link"
              title="Open in Google Maps"
            >
              <i class="fa-solid fa-map-location-dot"></i>
            </a>
            <ActionButton
              data-testid="shop-edit-button"
              icon="fa-solid fa-pen"
              variant="warning"
              title="Edit"
              @click="openEdit(shop)"
            />
            <ActionButton
              data-testid="shop-delete-button"
              icon="fa-solid fa-trash"
              variant="danger"
              title="Delete"
              @click="handleDelete(shop.id, shop.name)"
            />
          </div>
        </div>
      </template>
    </div>

    <AddEditCoffeeShopModal
      :visible="showAddModal || !!editShop"
      :edit-data="editShop"
      @close="handleModalClose"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { CoffeeShop, CoffeeShopCreate, CoffeeShopUpdate } from '@/api/client'
import { useCoffeeShopsStore } from '@/stores/coffeeShops'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import ActionButton from '@/components/ActionButton.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { COFFEE_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = COFFEE_SUBNAV
import AddEditCoffeeShopModal from '@/components/coffee/AddEditCoffeeShopModal.vue'

const store = useCoffeeShopsStore()
const { show: notify } = useNotifications()

const showAddModal = ref(false)
const editShop = ref<CoffeeShop | null>(null)

const cityFilterOptions = computed(() => [{ value: 'all', label: 'All Cities' }, ...store.cities.map((c) => ({ value: c, label: c }))])

const sortOptions = [
  { value: 'name', label: 'Sort: Name' },
  { value: 'rating', label: 'Sort: Rating' },
  { value: 'city', label: 'Sort: City' },
  { value: 'date_visited', label: 'Sort: Date Visited' },
]

onMounted(() => store.fetchAll())

function openEdit(shop: CoffeeShop) {
  editShop.value = shop
}

function handleModalClose() {
  showAddModal.value = false
  editShop.value = null
}

async function handleCreate(data: CoffeeShopCreate) {
  try {
    await store.create(data)
    notify(`${data.name} | added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Add failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: CoffeeShopUpdate) {
  const name = store.items.find((s) => s.id === id)?.name ?? 'Shop'
  try {
    await store.update(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await store.remove(id)
    notify(`${name} | deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Delete failed: ${detail}`, 'error')
  }
}
</script>
