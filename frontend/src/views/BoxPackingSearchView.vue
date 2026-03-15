<template>
  <div>
    <BoxPackingSubnav active="search" />

    <div class="searchbox">
      <form @submit.prevent="handleSearch">
        <label for="search_text"></label>
        <input
          id="search_text"
          ref="searchInput"
          v-model="query"
          type="text"
          class="button"
        />
        <button
          type="submit"
          class="button"
        >
          <span class="button__text">Search</span>
        </button>
      </form>
    </div>

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Searching...</h2>
      </div>
    </div>

    <div
      v-else-if="searched && store.searchResults.length === 0"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>No results found</h2>
      </div>
    </div>

    <div
      v-else-if="store.searchResults.length > 0"
      class="grid grid--one-column-full"
    >
      <ul class="search-results-boxes search-results-boxes__header">
        <li>Box Number</li>
        <li>Box Name</li>
        <li>Box Size</li>
        <li>Item</li>
        <li>Essential</li>
        <li>Warm</li>
        <li>Liquid</li>
      </ul>
      <ul
        v-for="(result, index) in store.searchResults"
        :key="index"
        class="search-results-boxes search-results-boxes__item"
      >
        <li>
          <RouterLink
            :to="`/box-packing/box/${result.box.id}`"
            class="search-results-boxes__link"
          >
            {{ result.box.number }}
          </RouterLink>
        </li>
        <li>
          <RouterLink
            :to="`/box-packing/box/${result.box.id}`"
            class="search-results-boxes__link"
          >
            {{ result.box.name }}
          </RouterLink>
        </li>
        <li>{{ result.box.size }}</li>
        <li>{{ result.item.name }}</li>
        <li class="packed-box-item__details--essential">
          <template v-if="result.item.essential">Essential</template>
        </li>
        <li class="packed-box-item__details--warm">
          <template v-if="result.item.warm">Warm</template>
        </li>
        <li class="packed-box-item__details--liquid">
          <template v-if="result.item.liquid">Liquid</template>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBoxPackingStore } from '@/stores/boxPacking'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import BoxPackingSubnav from '@/components/BoxPackingSubnav.vue'

const store = useBoxPackingStore()
const { show: notify } = useNotifications()

const query = ref('')
const searched = ref(false)
const searchInput = ref<HTMLInputElement | null>(null)

onMounted(() => {
  searchInput.value?.focus()
})

async function handleSearch() {
  if (!query.value.trim()) return
  searched.value = true
  try {
    await store.search(query.value.trim())
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Search failed: ${detail}`, 'error')
  }
}
</script>
