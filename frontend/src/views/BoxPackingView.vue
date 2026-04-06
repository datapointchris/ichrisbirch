<template>
  <div>
    <!-- Row 1: Search + View toggle -->
    <div class="box-controls">
      <input
        v-model="searchQuery"
        data-testid="box-search-input"
        type="text"
        class="textbox box-controls__search"
        placeholder="Search items..."
        @keyup.enter="handleSearch"
      />
      <button
        v-if="searchActive"
        data-testid="box-search-clear-button"
        class="button button--danger"
        @click="clearSearch"
      >
        <span class="button__text button__text--danger">Clear</span>
      </button>
      <button
        v-else
        data-testid="box-search-button"
        class="button"
        @click="handleSearch"
      >
        <span class="button__text">Search</span>
      </button>
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

    <!-- Row 2: Sort + Filter (labeled) -->
    <div class="box-controls">
      <span class="box-controls__label">
        Sort:
        <NeuSelect
          :model-value="store.sortField1"
          :options="SORT_OPTIONS"
          @update:model-value="store.sortField1 = $event"
        />
      </span>
      <span class="box-controls__label">
        Then:
        <NeuSelect
          :model-value="store.sortField2"
          :options="sortOptionsWithNone"
          @update:model-value="store.sortField2 = $event"
        />
      </span>
      <span class="box-controls__label">
        Filter:
        <NeuSelect
          :model-value="filterBy"
          :options="filterByOptions"
          data-testid="box-filter-input"
          @update:model-value="filterBy = $event"
        />
      </span>
    </div>

    <!-- Add buttons -->
    <div class="add-item-wrapper">
      <button
        data-testid="box-add-button"
        class="button"
        @click="showBoxModal = true"
      >
        <span class="button__text">Add Box</span>
      </button>
      <button
        data-testid="item-add-button"
        class="button"
        @click="openAddItem()"
      >
        <span class="button__text">Add Item</span>
      </button>
      <button
        data-testid="orphans-button"
        class="button"
        :class="store.orphans.length > 0 ? 'button--warning' : ''"
        :disabled="store.orphans.length === 0"
        @click="showOrphansModal = true"
      >
        <span
          class="button__text"
          :class="store.orphans.length > 0 ? 'button__text--warning' : ''"
        >
          Orphans ({{ store.orphans.length }})
        </span>
      </button>
    </div>

    <!-- Loading -->
    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Loading...</h2>
      </div>
    </div>

    <!-- Search Results -->
    <template v-else-if="searchActive">
      <div
        v-if="store.searchResults.length === 0"
        class="grid grid--one-column"
      >
        <div class="grid__item">
          <h2>No results for "{{ searchQuery }}"</h2>
        </div>
      </div>
      <div
        v-else
        class="grid grid--one-column-full"
      >
        <ul class="search-results-boxes search-results-boxes__header">
          <li>Box #</li>
          <li>Box Name</li>
          <li>Size</li>
          <li>Item</li>
          <li>Essential</li>
          <li>Warm</li>
          <li>Liquid</li>
        </ul>
        <ul
          v-for="(result, index) in store.searchResults"
          :key="index"
          data-testid="search-result-item"
          class="search-results-boxes search-results-boxes__item"
        >
          <li>{{ result.box.number }}</li>
          <li>{{ result.box.name }}</li>
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
    </template>

    <!-- Box List -->
    <template v-else>
      <div
        v-if="filteredBoxes.length === 0"
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
          v-for="box in filteredBoxes"
          :key="box.id"
          data-testid="box-item"
          class="grid__item"
        >
          <div class="packed-box__header">
            <h2 class="packed-box__title">Box {{ box.number }}: {{ box.name }}</h2>
            <div class="packed-box__actions">
              <ActionButton
                data-testid="box-edit-button"
                icon="fa-solid fa-pen-to-square"
                variant="warning"
                title="Edit box"
                @click="openEditBox(box)"
              />
              <ActionButton
                data-testid="box-delete-button"
                icon="fa-regular fa-trash-can"
                variant="danger"
                title="Delete box"
                @click="handleDeleteBox(box.id, box.name)"
              />
            </div>
          </div>
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

          <!-- Items always visible in block view -->
          <div class="box-contents">
            <div
              v-if="box.items.length === 0"
              class="box-contents__empty"
            >
              No items in this box.
            </div>
            <div class="box-contents__items">
              <div
                v-for="item in sortItems(box.items)"
                :key="item.id"
                data-testid="box-content-item"
                class="box-contents__item"
              >
                <span class="box-contents__item-name">{{ item.name }}</span>
                <span
                  v-if="item.essential"
                  class="packed-box-item__details--essential"
                  >Essential</span
                >
                <span
                  v-if="item.warm"
                  class="packed-box-item__details--warm"
                  >Warm</span
                >
                <span
                  v-if="item.liquid"
                  class="packed-box-item__details--liquid"
                  >Liquid</span
                >
                <span class="box-contents__item-actions">
                  <ActionButton
                    data-testid="item-orphan-button"
                    icon="fa-solid fa-arrow-up-from-bracket"
                    variant="warning"
                    title="Remove from box"
                    @click="handleOrphanItem(item.id, item.name, box.id)"
                  />
                  <ActionButton
                    data-testid="item-delete-button"
                    icon="fa-regular fa-trash-can"
                    variant="danger"
                    title="Delete item"
                    @click="handleDeleteItem(item.id, item.name, box.id)"
                  />
                </span>
              </div>
            </div>
            <div class="box-contents__add">
              <button
                data-testid="box-add-item-button"
                class="button button--small"
                @click="openAddItem(box.id)"
              >
                <span class="button__text">Add Item to Box</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Compact View -->
      <div v-else>
        <div
          v-for="box in filteredBoxes"
          :key="box.id"
          data-testid="box-item"
        >
          <div
            class="box-listing__row"
            @click="toggleExpand(box.id)"
          >
            <h3 class="box-listing__title">
              <span class="box-listing__link"> Box {{ box.number }}: {{ box.name }} </span>
            </h3>
            <span>Size: {{ box.size }}</span>
            <span>{{ box.items.length }} Item{{ box.items.length !== 1 ? 's' : '' }}</span>
            <span
              v-if="box.essential"
              class="box-listing__details--essential"
              >Essential</span
            >
            <span v-else>&nbsp;</span>
            <span
              v-if="box.warm"
              class="box-listing__details--warm"
              >Warm</span
            >
            <span v-else>&nbsp;</span>
            <span
              v-if="box.liquid"
              class="box-listing__details--liquid"
              >Liquid</span
            >
            <span v-else>&nbsp;</span>
            <span @click.stop>
              <ActionButton
                data-testid="box-edit-button"
                icon="fa-solid fa-pen-to-square"
                variant="warning"
                title="Edit box"
                @click="openEditBox(box)"
              />
            </span>
            <span @click.stop>
              <ActionButton
                data-testid="box-delete-button"
                icon="fa-regular fa-trash-can"
                variant="danger"
                title="Delete box"
                @click="handleDeleteBox(box.id, box.name)"
              />
            </span>
          </div>
          <!-- Expanded items in compact view -->
          <div
            v-if="expandedIds.has(box.id)"
            class="box-contents box-contents--compact"
          >
            <div
              v-if="box.items.length === 0"
              class="box-contents__empty"
            >
              No items in this box.
            </div>
            <div class="box-contents__items">
              <div
                v-for="item in sortItems(box.items)"
                :key="item.id"
                data-testid="box-content-item"
                class="box-contents__item"
              >
                <span class="box-contents__item-name">{{ item.name }}</span>
                <span
                  v-if="item.essential"
                  class="packed-box-item__details--essential"
                  >Essential</span
                >
                <span
                  v-if="item.warm"
                  class="packed-box-item__details--warm"
                  >Warm</span
                >
                <span
                  v-if="item.liquid"
                  class="packed-box-item__details--liquid"
                  >Liquid</span
                >
                <span class="box-contents__item-actions">
                  <ActionButton
                    data-testid="item-orphan-button"
                    icon="fa-solid fa-arrow-up-from-bracket"
                    variant="warning"
                    title="Remove from box"
                    @click="handleOrphanItem(item.id, item.name, box.id)"
                  />
                  <ActionButton
                    data-testid="item-delete-button"
                    icon="fa-regular fa-trash-can"
                    variant="danger"
                    title="Delete item"
                    @click="handleDeleteItem(item.id, item.name, box.id)"
                  />
                </span>
              </div>
            </div>
            <div class="box-contents__add">
              <button
                data-testid="box-add-item-button"
                class="button button--small"
                @click="openAddItem(box.id)"
              >
                <span class="button__text">Add Item to Box</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Modals -->
    <AddEditBoxModal
      :visible="showBoxModal"
      :edit-data="editBoxTarget"
      @close="closeBoxModal"
      @create="handleCreateBox"
      @update="handleUpdateBox"
    />

    <AddEditItemModal
      :visible="showItemModal"
      :boxes="store.sortedBoxes"
      :preselected-box-id="preselectedBoxId"
      :edit-data="null"
      @close="closeItemModal"
      @create="handleCreateItem"
    />

    <OrphansModal
      :visible="showOrphansModal"
      :orphans="store.orphans"
      :boxes="store.sortedBoxes"
      @close="showOrphansModal = false"
      @assign="handleAssignOrphan"
      @delete="handleDeleteOrphan"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBoxPackingStore, SORT_OPTIONS } from '@/stores/boxPacking'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Box, BoxCreate, BoxUpdate, BoxItem, BoxItemCreate, BoxSize } from '@/api/client'
import ActionButton from '@/components/ActionButton.vue'
import AddEditBoxModal from '@/components/box-packing/AddEditBoxModal.vue'
import AddEditItemModal from '@/components/box-packing/AddEditItemModal.vue'
import OrphansModal from '@/components/box-packing/OrphansModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const store = useBoxPackingStore()
const { show: notify } = useNotifications()

// Search
const searchQuery = ref('')
const searchActive = ref(false)

// Filter
const filterBy = ref<'all' | 'essential' | 'warm' | 'liquid'>('all')
const filterByOptions = [
  { value: 'all' as const, label: 'All' },
  { value: 'essential' as const, label: 'Essential' },
  { value: 'warm' as const, label: 'Warm' },
  { value: 'liquid' as const, label: 'Liquid' },
]
const sortOptionsWithNone = [{ value: '' as const, label: 'None' }, ...SORT_OPTIONS]

// Expand
const expandedIds = ref(new Set<number>())

// Box modal
const showBoxModal = ref(false)
const editBoxTarget = ref<{
  id: number
  name: string
  number?: number
  size: BoxSize
} | null>(null)

// Item modal
const showItemModal = ref(false)
const preselectedBoxId = ref<number | undefined>(undefined)

// Orphans modal
const showOrphansModal = ref(false)

const filteredBoxes = computed(() => {
  const boxes = store.sortedBoxes
  switch (filterBy.value) {
    case 'essential':
      return boxes.filter((b) => b.essential)
    case 'warm':
      return boxes.filter((b) => b.warm)
    case 'liquid':
      return boxes.filter((b) => b.liquid)
    default:
      return boxes
  }
})

onMounted(() => {
  store.fetchAll()
})

function sortItems(items: BoxItem[]): BoxItem[] {
  return [...items].sort((a, b) => a.name.localeCompare(b.name))
}

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

// Search
async function handleSearch() {
  if (!searchQuery.value.trim()) return
  try {
    await store.search(searchQuery.value.trim())
    searchActive.value = true
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Search failed: ${detail}`, 'error')
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchActive.value = false
  store.clearSearch()
}

// Box modal — editData no longer includes derived fields
function openEditBox(box: Box) {
  editBoxTarget.value = {
    id: box.id,
    name: box.name,
    number: box.number,
    size: box.size,
  }
  showBoxModal.value = true
}

function closeBoxModal() {
  showBoxModal.value = false
  editBoxTarget.value = null
}

async function handleCreateBox(data: BoxCreate) {
  try {
    await store.createBox(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add box: ${detail}`, 'error')
  }
}

async function handleUpdateBox(id: number, data: BoxUpdate) {
  const name = store.boxes.find((b) => b.id === id)?.name ?? 'Box'
  try {
    await store.updateBox(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update box: ${detail}`, 'error')
  }
}

async function handleDeleteBox(id: number, name: string) {
  try {
    await store.deleteBox(id)
    expandedIds.value.delete(id)
    await store.fetchOrphans()
    notify(`Box "${name}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete box: ${detail}`, 'error')
  }
}

// Item modal
function openAddItem(boxId?: number) {
  preselectedBoxId.value = boxId
  showItemModal.value = true
}

function closeItemModal() {
  showItemModal.value = false
  preselectedBoxId.value = undefined
}

async function handleCreateItem(data: BoxItemCreate) {
  try {
    await store.createItem(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add item: ${detail}`, 'error')
  }
}

async function handleOrphanItem(itemId: number, itemName: string, boxId: number) {
  try {
    await store.orphanItem(itemId, boxId)
    await store.fetchOrphans()
    notify(`"${itemName}" removed from box`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to orphan item: ${detail}`, 'error')
  }
}

async function handleDeleteItem(itemId: number, itemName: string, boxId: number) {
  try {
    await store.deleteItem(itemId, boxId)
    notify(`"${itemName}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete item: ${detail}`, 'error')
  }
}

// Orphan actions
async function handleAssignOrphan(itemId: number, boxId: number) {
  const itemName = store.orphans.find((o) => o.id === itemId)?.name ?? 'Item'
  const boxName = store.boxes.find((b) => b.id === boxId)?.name ?? 'box'
  try {
    await store.assignOrphanToBox(itemId, boxId)
    notify(`${itemName} assigned to ${boxName}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to assign item: ${detail}`, 'error')
  }
}

async function handleDeleteOrphan(id: number, name: string) {
  try {
    await store.deleteOrphan(id)
    notify(`"${name}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete orphan: ${detail}`, 'error')
  }
}
</script>
