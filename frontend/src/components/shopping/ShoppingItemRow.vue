<template>
  <div
    class="shopping-item"
    :class="{ 'shopping-item--checking': checking }"
    data-testid="shopping-item"
    :data-item-id="item.id"
  >
    <button
      type="button"
      class="shopping-item__check"
      data-testid="shopping-item-check"
      :aria-label="`Bought ${item.name}`"
      :disabled="checking"
      @click="emit('check', item)"
    >
      <i class="fa-solid fa-check"></i>
    </button>
    <div
      class="shopping-item__text"
      @click="emit('edit', item)"
    >
      <button
        type="button"
        class="shopping-item__name"
        data-testid="shopping-item-edit"
      >
        {{ item.name }}
      </button>
      <span
        v-if="item.note"
        class="shopping-item__note"
        data-testid="shopping-item-note"
      >
        <template
          v-for="(part, index) in noteParts(item.note)"
          :key="index"
        >
          <a
            v-if="part.href"
            :href="part.href"
            target="_blank"
            rel="noopener noreferrer"
            class="shopping-item__link"
            @click.stop
            >{{ part.text }}</a
          >
          <template v-else>{{ part.text }}</template>
        </template>
      </span>
    </div>
    <span
      class="shopping-item__grip"
      data-testid="shopping-item-grip"
      aria-hidden="true"
    >
      <i class="fa-solid fa-grip-lines"></i>
    </span>
  </div>
</template>

<script setup lang="ts">
import type { ShoppingItem } from '@/api/client'

defineProps<{
  item: ShoppingItem
  checking?: boolean
}>()

const emit = defineEmits<{
  check: [item: ShoppingItem]
  edit: [item: ShoppingItem]
}>()

const URL_PATTERN = /(https?:\/\/\S+)/

/** A note split into plain text and links, each link shown by its host so a long URL fits a phone. */
function noteParts(note: string): { text: string; href: string | null }[] {
  return note
    .split(URL_PATTERN)
    .filter((part) => part !== '')
    .map((part) => {
      if (!URL_PATTERN.test(part)) return { text: part, href: null }
      try {
        return { text: new URL(part).hostname, href: part }
      } catch {
        return { text: part, href: null }
      }
    })
}
</script>
