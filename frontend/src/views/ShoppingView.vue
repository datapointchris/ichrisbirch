<template>
  <div
    class="shopping"
    data-testid="shopping-page"
  >
    <div class="shopping__add-bar">
      <form
        class="shopping__add-form"
        @submit.prevent="quickAdd"
      >
        <input
          ref="addInput"
          v-model="typed"
          type="text"
          class="textbox shopping__add-input"
          data-testid="shopping-add-input"
          placeholder="Add item…"
          aria-label="Add item"
          autocomplete="off"
          enterkeyhint="done"
        />
        <button
          type="button"
          class="shopping__icon-button"
          data-testid="shopping-add-button"
          aria-label="Add with a note or section"
          @click="openAdd"
        >
          <i class="fa-solid fa-plus"></i>
        </button>
        <span
          class="shopping__total"
          data-testid="shopping-total"
          :aria-label="`${store.needed.length} on the list`"
        >
          {{ store.needed.length }}
        </span>
      </form>
      <p
        v-if="lastAdded"
        class="shopping__last-added"
        data-testid="shopping-last-added"
      >
        {{ lastAdded }}
      </p>
      <ul
        v-if="suggestions.length"
        class="shopping__suggestions"
        data-testid="shopping-suggestions"
      >
        <li
          v-for="item in suggestions"
          :key="item.id"
        >
          <button
            type="button"
            class="shopping__suggestion"
            data-testid="shopping-suggestion"
            @mousedown.prevent
            @click="addKnown(item)"
          >
            <span>{{ item.name }}</span>
            <span class="shopping__suggestion-where">{{ item.is_needed ? 'on the list' : (item.section_name ?? 'Unsorted') }}</span>
          </button>
        </li>
      </ul>
      <div
        v-else-if="store.buyAgain.length"
        class="shopping-buy-again"
        data-testid="shopping-buy-again"
      >
        <span class="shopping-buy-again__label">Buy again</span>
        <button
          v-for="item in store.buyAgain"
          :key="item.id"
          type="button"
          class="shopping-buy-again__chip"
          data-testid="shopping-buy-again-chip"
          @click="addKnown(item)"
        >
          {{ item.name }}
        </button>
      </div>
    </div>

    <p
      v-if="store.loading && store.catalog.length === 0"
      class="shopping__empty"
    >
      Loading…
    </p>
    <p
      v-else-if="store.needed.length === 0"
      class="shopping__empty"
      data-testid="shopping-empty"
    >
      Nothing on the list
    </p>

    <section
      v-show="unsortedItems.length > 0 || dragging"
      class="shopping-section shopping-section--unsorted"
      data-testid="shopping-section"
      :data-section="UNSORTED_KEY"
    >
      <ShoppingSectionHeader
        :section="null"
        :count="unsortedItems.length"
        :collapsed="isCollapsed(UNSORTED_KEY)"
        @toggle="toggle(UNSORTED_KEY)"
      />
      <draggable
        v-show="!isCollapsed(UNSORTED_KEY)"
        :list="unsortedItems"
        item-key="id"
        group="shopping-items"
        handle=".shopping-item__grip"
        ghost-class="shopping-item--ghost"
        :animation="150"
        class="shopping-section__items"
        data-testid="shopping-section-items"
        @start="dragging = true"
        @end="dragging = false"
        @change="onItemChange(null, $event)"
      >
        <template #item="{ element }">
          <ShoppingItemRow
            :item="element"
            :checking="checking.has(element.id)"
            @check="checkOff"
            @edit="openEdit"
          />
        </template>
      </draggable>
    </section>

    <draggable
      :list="localSections"
      item-key="id"
      handle=".shopping-section__grip"
      ghost-class="shopping-section--ghost"
      :animation="150"
      class="shopping__sections"
      @change="onSectionChange"
    >
      <template #item="{ element: section }">
        <section
          class="shopping-section"
          data-testid="shopping-section"
          :data-section="section.id"
        >
          <ShoppingSectionHeader
            :section="section"
            :count="itemsOf(section.id).length"
            :collapsed="isCollapsed(section.id)"
            @toggle="toggle(section.id)"
            @rename="renameSection(section, $event)"
            @delete="deleteSection(section)"
          />
          <draggable
            v-show="!isCollapsed(section.id)"
            :list="itemsOf(section.id)"
            item-key="id"
            group="shopping-items"
            handle=".shopping-item__grip"
            ghost-class="shopping-item--ghost"
            :animation="150"
            class="shopping-section__items"
            data-testid="shopping-section-items"
            @start="dragging = true"
            @end="dragging = false"
            @change="onItemChange(section.id, $event)"
          >
            <template #item="{ element }">
              <ShoppingItemRow
                :item="element"
                :checking="checking.has(element.id)"
                @check="checkOff"
                @edit="openEdit"
              />
            </template>
          </draggable>
        </section>
      </template>
    </draggable>

    <form
      v-if="addingSection"
      class="shopping__new-section"
      @submit.prevent="createSection"
    >
      <input
        ref="sectionInput"
        v-model="newSectionName"
        type="text"
        class="textbox"
        data-testid="shopping-new-section-input"
        placeholder="Section name"
        aria-label="New section name"
        autocomplete="off"
        @keydown.esc.prevent="addingSection = false"
        @blur="createSection"
      />
    </form>
    <button
      v-else
      type="button"
      class="shopping__new-section-button"
      data-testid="shopping-new-section-button"
      @click="startNewSection"
    >
      <i class="fa-solid fa-plus"></i> New section
    </button>

    <section
      v-if="store.recentPurchases.length"
      class="shopping-section shopping-section--bought"
      data-testid="shopping-recently-bought"
    >
      <div class="shopping-section__header">
        <button
          type="button"
          class="shopping-section__toggle"
          data-testid="shopping-bought-toggle"
          :aria-expanded="!isCollapsed(BOUGHT_KEY)"
          @click="toggle(BOUGHT_KEY)"
        >
          <i
            class="fa-solid"
            :class="isCollapsed(BOUGHT_KEY) ? 'fa-caret-right' : 'fa-caret-down'"
          ></i>
        </button>
        <span class="shopping-section__name shopping-section__name--unsorted">Recently bought</span>
        <span class="shopping-section__count">{{ store.recentPurchases.length }}</span>
      </div>
      <div v-show="!isCollapsed(BOUGHT_KEY)">
        <template
          v-for="day in recentDays"
          :key="day.key"
        >
          <h3
            class="shopping-bought__day"
            data-testid="shopping-bought-day"
          >
            {{ day.label }}
          </h3>
          <ul class="shopping-section__items">
            <li
              v-for="purchase in day.purchases"
              :key="purchase.id"
            >
              <button
                type="button"
                class="shopping-bought"
                data-testid="shopping-bought-row"
                :aria-label="`Put ${purchase.item_name} back on the list`"
                @click="undoPurchase(purchase)"
              >
                <i class="fa-solid fa-rotate-left"></i>
                <span class="shopping-bought__name">{{ purchase.item_name }}</span>
                <span
                  v-if="purchase.section_name"
                  class="shopping-bought__section"
                  >{{ purchase.section_name }}</span
                >
              </button>
            </li>
          </ul>
        </template>
      </div>
    </section>

    <AddEditShoppingItemModal
      :visible="showModal"
      :sections="store.sections"
      :catalog="store.catalog"
      :edit-data="editTarget"
      :initial-name="modalName"
      @close="closeModal"
      @create="createFromModal"
      @update="updateFromModal"
      @remove="takeOffList"
      @delete="forgetItem"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { ApiError } from '@/api/errors'
import type { ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate, ShoppingPurchase, ShoppingSection } from '@/api/client'
import { useNotifications } from '@/composables/useNotifications'
import { UNSORTED_KEY, itemMoveFor, purchasesByDay, sectionMoveFor, suggestionsFor, useShoppingStore } from '@/stores/shopping'
import AddEditShoppingItemModal from '@/components/shopping/AddEditShoppingItemModal.vue'
import ShoppingItemRow from '@/components/shopping/ShoppingItemRow.vue'
import ShoppingSectionHeader from '@/components/shopping/ShoppingSectionHeader.vue'

interface DraggableChange<T> {
  added?: { element: T; newIndex: number }
  moved?: { element: T; oldIndex: number; newIndex: number }
  removed?: { element: T; oldIndex: number }
}

const BOUGHT_KEY = 'recently-bought'
const COLLAPSED_STORAGE_KEY = 'shopping-collapsed'
// Long enough to see the strike-through land before the row leaves.
const CHECK_OFF_DELAY_MS = 300

const store = useShoppingStore()
const { show: notify } = useNotifications()
const recentDays = computed(() => purchasesByDay(store.recentPurchases))

const addInput = ref<HTMLInputElement | null>(null)
const sectionInput = ref<HTMLInputElement | null>(null)
const typed = ref('')
const lastAdded = ref('')
const dragging = ref(false)
const checking = ref(new Set<string>())
const addingSection = ref(false)
const newSectionName = ref('')
const showModal = ref(false)
const editTarget = ref<ShoppingItem | null>(null)
const modalName = ref('')

// Draggable mutates the lists it is given, so it gets copies the store rebuilds after every write.
const unsortedItems = ref<ShoppingItem[]>([])
const localSections = ref<ShoppingSection[]>([])
const sectionItems = ref<Record<string, ShoppingItem[]>>({})

watch(
  () => store.groups,
  (groups) => {
    const bySection: Record<string, ShoppingItem[]> = {}
    for (const group of groups) {
      if (group.section) bySection[group.section.id] = [...group.items]
      else unsortedItems.value = [...group.items]
    }
    sectionItems.value = bySection
    localSections.value = groups.flatMap((group) => (group.section ? [group.section] : []))
  },
  { immediate: true }
)

function itemsOf(sectionId: string): ShoppingItem[] {
  return sectionItems.value[sectionId] ?? []
}

const suggestions = computed(() => suggestionsFor(typed.value, store.catalog))

function readCollapsed(): Set<string> {
  try {
    const saved = localStorage.getItem(COLLAPSED_STORAGE_KEY)
    return new Set(saved ? (JSON.parse(saved) as string[]) : [])
  } catch {
    return new Set()
  }
}

const collapsed = ref(readCollapsed())

function isCollapsed(key: string): boolean {
  return collapsed.value.has(key)
}

function toggle(key: string) {
  if (collapsed.value.has(key)) collapsed.value.delete(key)
  else collapsed.value.add(key)
  try {
    localStorage.setItem(COLLAPSED_STORAGE_KEY, JSON.stringify([...collapsed.value]))
  } catch {
    // A private window refuses storage; the sections then open expanded next time.
  }
}

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`Could not ${action}: ${detail}`, 'error')
}

function whereItWent(item: ShoppingItem): string {
  return `${item.name} → ${item.section_name ?? 'Unsorted'}`
}

onMounted(async () => {
  try {
    await store.fetchAll()
  } catch (e) {
    failure('load the shopping list', e)
  }
})

async function add(input: ShoppingItemCreate) {
  try {
    const item = await store.addItem(input)
    lastAdded.value = whereItWent(item)
  } catch (e) {
    failure(`add ${input.name}`, e)
  }
}

async function quickAdd() {
  const name = typed.value.trim()
  if (!name) return
  typed.value = ''
  addInput.value?.focus()
  await add({ name })
}

async function addKnown(item: ShoppingItem) {
  typed.value = ''
  addInput.value?.focus()
  await add({ name: item.name })
}

async function checkOff(item: ShoppingItem) {
  if (checking.value.has(item.id)) return
  checking.value.add(item.id)
  await new Promise((resolve) => setTimeout(resolve, CHECK_OFF_DELAY_MS))
  try {
    await store.checkOff(item)
  } catch (e) {
    failure(`check off ${item.name}`, e)
  } finally {
    checking.value.delete(item.id)
  }
}

async function undoPurchase(purchase: ShoppingPurchase) {
  try {
    await store.undoPurchase(purchase)
  } catch (e) {
    failure(`put ${purchase.item_name} back`, e)
  }
}

async function onItemChange(sectionId: string | null, event: DraggableChange<ShoppingItem>) {
  const change = event.added ?? event.moved
  if (!change) return
  const list = sectionId ? itemsOf(sectionId) : unsortedItems.value
  try {
    await store.moveItem(change.element.id, itemMoveFor(sectionId, list, change.newIndex))
  } catch (e) {
    failure(`move ${change.element.name}`, e)
  }
}

async function onSectionChange(event: DraggableChange<ShoppingSection>) {
  if (!event.moved) return
  const neighbor = sectionMoveFor(localSections.value, event.moved.newIndex)
  if (!neighbor) return
  try {
    await store.moveSection(event.moved.element.id, neighbor)
  } catch (e) {
    failure(`move ${event.moved.element.name}`, e)
  }
}

async function startNewSection() {
  newSectionName.value = ''
  addingSection.value = true
  await nextTick()
  sectionInput.value?.focus()
}

async function createSection() {
  if (!addingSection.value) return
  addingSection.value = false
  const name = newSectionName.value.trim()
  if (!name) return
  try {
    await store.createSection(name)
  } catch (e) {
    failure(`create ${name}`, e)
  }
}

async function renameSection(section: ShoppingSection, name: string) {
  try {
    await store.renameSection(section.id, name)
  } catch (e) {
    failure(`rename ${section.name}`, e)
  }
}

async function deleteSection(section: ShoppingSection) {
  try {
    await store.deleteSection(section.id)
    notify(`${section.name} deleted; its items are in Unsorted`, 'success')
  } catch (e) {
    failure(`delete ${section.name}`, e)
  }
}

function openAdd() {
  editTarget.value = null
  modalName.value = typed.value.trim()
  showModal.value = true
}

function openEdit(item: ShoppingItem) {
  editTarget.value = item
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
  modalName.value = ''
}

async function createFromModal(data: ShoppingItemCreate) {
  typed.value = ''
  await add(data)
}

async function updateFromModal(id: string, data: ShoppingItemUpdate) {
  try {
    await store.updateItem(id, data)
  } catch (e) {
    failure(`save ${data.name ?? 'the item'}`, e)
  }
}

async function takeOffList(id: string) {
  try {
    await store.updateItem(id, { is_needed: false })
  } catch (e) {
    failure('take it off the list', e)
  }
}

async function forgetItem(id: string) {
  const name = store.catalog.find((item) => item.id === id)?.name ?? 'the item'
  try {
    await store.deleteItem(id)
    notify(`${name} forgotten`, 'success')
  } catch (e) {
    failure(`forget ${name}`, e)
  }
}
</script>
