<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column">
      <div
        v-if="store.loading"
        class="autofun-completed__empty"
      >
        Loading...
      </div>

      <template v-else>
        <div class="autofun-completed__list">
          <div
            v-for="item in completedItems"
            :key="item.id"
            class="autofun-completed__item"
            data-testid="autofun-completed-item"
          >
            <div class="autofun-completed__item-content">
              <span class="autofun-completed__item-name">{{ item.name }}</span>
              <span
                v-if="item.notes"
                class="autofun-completed__item-notes"
                >{{ item.notes }}</span
              >
            </div>
            <span
              v-if="item.completed_date"
              class="autofun-completed__item-date"
              >{{ formatDate(item.completed_date, 'shortDate') }}</span
            >
          </div>
          <div
            v-if="completedItems.length === 0"
            class="autofun-completed__empty"
          >
            No completed activities yet.
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAutoFunStore } from '@/stores/autofun'
import { formatDate } from '@/composables/formatDate'
import AppSubnav from '@/components/AppSubnav.vue'
import { AUTOFUN_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = AUTOFUN_SUBNAV

const store = useAutoFunStore()

const completedItems = computed(() =>
  [...store.completedItems]
    .filter((i) => i.completed_date)
    .sort((a, b) => new Date(b.completed_date!).getTime() - new Date(a.completed_date!).getTime())
)

onMounted(async () => {
  await store.fetchAll()
})
</script>

<style scoped>
.autofun-completed__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-s);
  margin-top: var(--space-m);
}

.autofun-completed__item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-s) var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  gap: var(--space-m);
}

.autofun-completed__item-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
}

.autofun-completed__item-name {
  font-size: var(--fs-500);
  color: var(--clr-primary-300);
}

.autofun-completed__item-notes {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
}

.autofun-completed__item-date {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  white-space: nowrap;
}

.autofun-completed__empty {
  color: var(--clr-gray-500);
  font-style: italic;
}
</style>
