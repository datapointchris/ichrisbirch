<template>
  <ListingModal
    :visible="visible"
    @close="handleModalClose"
  >
    <template #default="{ handleClose }">
      <div class="listing-modal__content">
        <h2 class="packed-box__title listing-modal__title">Orphaned Items ({{ orphans.length }})</h2>

        <div class="listing-modal__scrollable">
          <div
            v-if="orphans.length === 0"
            class="orphans-modal__empty"
          >
            No orphaned items.
          </div>

          <div
            v-for="orphan in sortedOrphans"
            :key="orphan.id"
            data-testid="orphan-item"
            class="orphans-modal__item"
          >
            <span class="orphans-modal__name">{{ orphan.name }}</span>
            <span
              v-if="orphan.essential"
              class="packed-box-item__details--essential"
              >Essential</span
            >
            <span v-else></span>
            <span
              v-if="orphan.warm"
              class="packed-box-item__details--warm"
              >Warm</span
            >
            <span v-else></span>
            <span
              v-if="orphan.liquid"
              class="packed-box-item__details--liquid"
              >Liquid</span
            >
            <span v-else></span>
            <NeuSelect
              :model-value="null"
              :options="boxOptions"
              :data-testid="`orphan-assign-${orphan.id}`"
              placeholder="Assign"
              @update:model-value="handleAssign(orphan.id, $event as number)"
            >
              <template #option="{ option }">
                <span>{{ option.label }}</span>
                <span class="orphans-modal__box-detail">{{ option.size }}</span>
              </template>
            </NeuSelect>
            <button
              data-testid="orphan-delete-button"
              class="button--hidden"
              @click="$emit('delete', orphan.id, orphan.name)"
            >
              <i class="button-icon danger fa-regular fa-trash-can"></i>
            </button>
          </div>
        </div>

        <div class="listing-modal__buttons">
          <button
            type="button"
            data-testid="orphans-close-button"
            class="button"
            @click="handleClose()"
          >
            <span class="button__text">Close</span>
          </button>
        </div>
      </div>
    </template>
  </ListingModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Box, BoxItem } from '@/api/client'
import ListingModal from '@/components/ListingModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const props = defineProps<{
  visible: boolean
  orphans: BoxItem[]
  boxes: Box[]
}>()

const emit = defineEmits<{
  close: []
  assign: [itemId: number, boxId: number]
  delete: [id: number, name: string]
}>()

const sortedOrphans = computed(() => [...props.orphans].sort((a, b) => a.name.localeCompare(b.name)))

const boxOptions = computed(() =>
  props.boxes.map((b) => ({
    value: b.id,
    label: `Box ${b.number}: ${b.name}`,
    size: b.size,
  }))
)

function handleModalClose() {
  emit('close')
}

function handleAssign(orphanId: number, boxId: number) {
  emit('assign', orphanId, boxId)
}
</script>

<style scoped>
.orphans-modal__empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-s) 0;
}

.orphans-modal__item {
  display: grid;
  grid-template-columns: 3fr 1fr 1fr 1fr 2fr auto;
  align-items: center;
  gap: var(--space-m);
  padding: var(--space-m);
  border-bottom: 1px solid var(--clr-gray-800);
}

.orphans-modal__item:last-of-type {
  border-bottom: none;
}

.orphans-modal__name {
  font-weight: bold;
  text-align: left;
}

.orphans-modal__box-detail {
  font-size: var(--fs-300);
  opacity: 0.7;
  margin-left: var(--space-xs);
}
</style>
