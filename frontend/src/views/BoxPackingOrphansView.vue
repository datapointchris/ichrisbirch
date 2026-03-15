<template>
  <div>
    <BoxPackingSubnav active="orphans" />

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Loading...</h2>
      </div>
    </div>

    <div
      v-else-if="store.orphans.length === 0"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>No Orphaned Items</h2>
      </div>
    </div>

    <template v-else>
      <div class="grid grid--one-column-wide">
        <ul class="search-results-orphans search-results-orphans__header">
          <li>Item</li>
          <li>Essential</li>
          <li>Warm</li>
          <li>Liquid</li>
          <li>Box</li>
          <li>Delete</li>
        </ul>
        <ul
          v-for="orphan in sortedOrphans"
          :key="orphan.id"
          class="search-results-orphans search-results-orphans__item"
        >
          <li>{{ orphan.name }}</li>
          <li class="packed-box-item__details--essential">
            <template v-if="orphan.essential">Essential</template>
          </li>
          <li class="packed-box-item__details--warm">
            <template v-if="orphan.warm">Warm</template>
          </li>
          <li class="packed-box-item__details--liquid">
            <template v-if="orphan.liquid">Liquid</template>
          </li>
          <li>
            <select
              class="button"
              @change="handleAssign(orphan.id, $event)"
            >
              <option
                value=""
                selected
                disabled
                hidden
              >
                Add to Box
              </option>
              <option
                v-for="box in store.sortedBoxes"
                :key="box.id"
                :value="box.id"
              >
                Box {{ box.number }}: {{ box.name }}
              </option>
            </select>
          </li>
          <li>
            <button
              class="button--hidden"
              @click="handleDelete(orphan.id, orphan.name)"
            >
              <i class="button-icon danger fa-regular fa-trash-can"></i>
            </button>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBoxPackingStore } from '@/stores/boxPacking'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import BoxPackingSubnav from '@/components/BoxPackingSubnav.vue'

const store = useBoxPackingStore()
const { show: notify } = useNotifications()

const sortedOrphans = computed(() => [...store.orphans].sort((a, b) => a.name.localeCompare(b.name)))

onMounted(async () => {
  await Promise.all([store.fetchOrphans(), store.fetchBoxes()])
})

async function handleAssign(itemId: number, event: Event) {
  const select = event.target as HTMLSelectElement
  const boxId = Number(select.value)
  if (isNaN(boxId)) return
  try {
    await store.assignOrphanToBox(itemId, boxId)
    notify('Item assigned to box', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to assign item: ${detail}`, 'error')
  }
  // Reset select to placeholder
  select.value = ''
}

async function handleDelete(id: number, name: string) {
  try {
    await store.deleteOrphan(id)
    notify(`Item "${name}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete item: ${detail}`, 'error')
  }
}
</script>
