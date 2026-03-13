<template>
  <div class="countdowns">
    <h1>Countdowns</h1>
    <div
      v-if="store.loading"
      class="loading"
    >
      Loading...
    </div>
    <div
      v-else-if="store.error"
      class="error"
    >
      {{ store.error }}
    </div>
    <div
      v-else
      class="countdowns__list"
    >
      <p v-if="store.sortedCountdowns.length === 0">No countdowns yet.</p>
      <div
        v-for="countdown in store.sortedCountdowns"
        :key="countdown.id"
        class="countdown-card"
      >
        <h3>{{ countdown.name }}</h3>
        <p class="countdown-card__date">{{ countdown.due_date }}</p>
        <p
          v-if="countdown.notes"
          class="countdown-card__notes"
        >
          {{ countdown.notes }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useCountdownsStore } from '@/stores/countdowns'

const store = useCountdownsStore()

onMounted(() => {
  store.fetchAll()
})
</script>
