<template>
  <div class="stats-cards">
    <div
      v-for="card in cards"
      :key="card.label"
      class="stats-cards__card"
    >
      <div class="stats-cards__value">{{ card.value }}</div>
      <div class="stats-cards__label">{{ card.label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface StatsCard {
  label: string
  value: string | number
}

defineProps<{ cards: StatsCard[] }>()
</script>

<style scoped>
.stats-cards {
  display: flex;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.stats-cards__card {
  flex: 1;
  min-width: 100px;
  padding: var(--space-s) var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  text-align: center;
}

.stats-cards__value {
  font-size: var(--fs-700);
  font-weight: 700;
  color: var(--clr-primary-300);
}

.stats-cards__label {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  margin-top: var(--space-3xs);
}
</style>
