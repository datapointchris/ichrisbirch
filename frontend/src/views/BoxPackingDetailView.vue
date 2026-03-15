<template>
  <div>
    <BoxPackingSubnav active="detail" />

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Loading...</h2>
      </div>
    </div>

    <div
      v-else-if="!box"
      class="grid grid--one-column"
    >
      <div class="grid__item">
        <h2>Box not found</h2>
      </div>
    </div>

    <template v-else>
      <div class="grid grid--one-column-wide">
        <div class="grid__item">
          <!-- Box Header -->
          <div v-if="!editing">
            <h1 class="packed-box__title">Box {{ box.number }}: {{ box.name }}</h1>
            <h2>Size: {{ box.size }}</h2>
            <h3>
              <button
                class="button--hidden"
                @click="editing = true"
              >
                <i class="button-icon warning fa-solid fa-pen-to-square"></i>
              </button>
            </h3>
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

          <!-- Inline Edit Form -->
          <div v-else>
            <form
              class="add-item-form"
              @submit.prevent="handleEditBox"
            >
              <div class="add-item-form__item">
                <label for="edit_name">Name:</label>
                <input
                  id="edit_name"
                  v-model="editForm.name"
                  type="text"
                  class="textbox"
                  required
                />
              </div>
              <div class="add-item-form__item">
                <label for="edit_number">Number:</label>
                <input
                  id="edit_number"
                  v-model="editForm.number"
                  type="number"
                  class="textbox"
                />
              </div>
              <div class="add-item-form__item">
                <label for="edit_size">Size:</label>
                <select
                  id="edit_size"
                  v-model="editForm.size"
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
              <div class="add-item-form__item">
                <button
                  type="submit"
                  class="button"
                >
                  <span class="button__text">Save</span>
                </button>
                <button
                  type="button"
                  class="button"
                  @click="cancelEdit"
                >
                  <span class="button__text">Cancel</span>
                </button>
              </div>
            </form>
          </div>

          <!-- Items Grid -->
          <div class="grid grid--two-columns-nested">
            <div
              v-for="item in sortedItems"
              :key="item.id"
              class="grid__item"
            >
              <h3>{{ item.name }}</h3>
              <div class="packed-box-item__details">
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
              </div>
              <div>
                <button
                  class="button--hidden"
                  @click="handleOrphanItem(item.id, item.name)"
                >
                  <i class="button-icon warning fa-solid fa-arrow-up-from-bracket"></i>
                </button>
                <button
                  class="button--hidden"
                  @click="handleDeleteItem(item.id, item.name)"
                >
                  <i class="button-icon danger fa-regular fa-trash-can"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Add Item Form -->
          <div class="add-item-wrapper">
            <form
              class="add-item-form"
              @submit.prevent="handleAddItem"
            >
              <div class="add-item-form__item add-item-form__item--full-width">
                <h3>Add Item:</h3>
              </div>
              <div class="add-item-form__item add-item-form__item--full-width">
                <label for="item_name">Name:</label>
                <input
                  id="item_name"
                  v-model="itemForm.name"
                  type="text"
                  class="textbox"
                  required
                />
              </div>
              <div class="add-item-form__item add-item-form__item--full-width">
                <div class="packed-box-item__details">
                  <span>
                    <label
                      for="item_essential"
                      class="packed-box__details--essential"
                      >Essential</label
                    >
                    <input
                      id="item_essential"
                      v-model="itemForm.essential"
                      type="checkbox"
                    />
                  </span>
                  <span>
                    <label
                      for="item_warm"
                      class="packed-box__details--warm"
                      >Warm</label
                    >
                    <input
                      id="item_warm"
                      v-model="itemForm.warm"
                      type="checkbox"
                    />
                  </span>
                  <span>
                    <label
                      for="item_liquid"
                      class="packed-box__details--liquid"
                      >Liquid</label
                    >
                    <input
                      id="item_liquid"
                      v-model="itemForm.liquid"
                      type="checkbox"
                    />
                  </span>
                </div>
              </div>
              <div class="add-item-form__item add-item-form__item--full-width">
                <button
                  type="submit"
                  class="button"
                >
                  <span class="button__text">Add Item</span>
                </button>
              </div>
            </form>
          </div>

          <!-- Delete Box -->
          <div>
            <button
              class="button button--danger"
              @click="handleDeleteBox"
            >
              <span class="button__text button__text--danger">Delete Box</span>
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBoxPackingStore, BOX_SIZES } from '@/stores/boxPacking'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import BoxPackingSubnav from '@/components/BoxPackingSubnav.vue'
import type { Box, BoxSize } from '@/api/client'

const route = useRoute()
const router = useRouter()
const store = useBoxPackingStore()
const { show: notify } = useNotifications()

const box = ref<Box | null>(null)
const editing = ref(false)

const editForm = reactive({
  name: '',
  number: '' as string | number,
  size: 'Medium' as BoxSize,
})

const itemForm = reactive({
  name: '',
  essential: false,
  warm: false,
  liquid: false,
})

const sortedItems = computed(() => {
  if (!box.value) return []
  return [...box.value.items].sort((a, b) => a.name.localeCompare(b.name))
})

async function loadBox() {
  const id = Number(route.params.id)
  if (isNaN(id)) return
  try {
    box.value = await store.fetchBox(id)
    populateEditForm()
  } catch {
    box.value = null
  }
}

function populateEditForm() {
  if (!box.value) return
  editForm.name = box.value.name
  editForm.number = box.value.number ?? ''
  editForm.size = box.value.size
}

function cancelEdit() {
  editing.value = false
  populateEditForm()
}

onMounted(loadBox)

watch(
  () => route.params.id,
  () => loadBox()
)

async function handleEditBox() {
  if (!box.value) return
  try {
    const updated = await store.updateBox(box.value.id, {
      name: editForm.name.trim(),
      number: editForm.number ? Number(editForm.number) : undefined,
      size: editForm.size,
    })
    if (updated) {
      box.value = updated
    }
    editing.value = false
    notify('Box updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update box: ${detail}`, 'error')
  }
}

async function handleAddItem() {
  if (!box.value || !itemForm.name.trim()) return
  try {
    await store.createItem({
      box_id: box.value.id,
      name: itemForm.name.trim(),
      essential: itemForm.essential,
      warm: itemForm.warm,
      liquid: itemForm.liquid,
    })
    // Re-fetch box to get updated items and derived attributes
    box.value = await store.fetchBox(box.value.id)
    notify('Item added', 'success')
    itemForm.name = ''
    itemForm.essential = false
    itemForm.warm = false
    itemForm.liquid = false
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add item: ${detail}`, 'error')
  }
}

async function handleDeleteItem(itemId: number, itemName: string) {
  if (!box.value) return
  try {
    await store.deleteItem(itemId, box.value.id)
    box.value = await store.fetchBox(box.value.id)
    notify(`Item "${itemName}" deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete item: ${detail}`, 'error')
  }
}

async function handleOrphanItem(itemId: number, itemName: string) {
  if (!box.value) return
  try {
    await store.orphanItem(itemId, box.value.id)
    box.value = await store.fetchBox(box.value.id)
    notify(`Item "${itemName}" removed from box`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to orphan item: ${detail}`, 'error')
  }
}

async function handleDeleteBox() {
  if (!box.value) return
  const name = box.value.name
  try {
    await store.deleteBox(box.value.id)
    notify(`Box "${name}" deleted`, 'success')
    router.push('/box-packing')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete box: ${detail}`, 'error')
  }
}
</script>
