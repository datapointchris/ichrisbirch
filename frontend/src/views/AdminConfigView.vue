<template>
  <div>
    <div class="admin-section">
      <h2>Environment Configuration</h2>
      <div
        v-if="store.configLoading"
        class="admin-empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.config.length === 0"
        class="admin-empty"
      >
        No configuration loaded
      </div>
      <div
        v-else
        class="config-sections"
      >
        <details
          v-for="section in store.config"
          :key="section.name"
          class="config-section"
          :open="section.name === '_general'"
        >
          <summary class="config-section__header">
            {{ formatSectionName(section.name) }}
            <span class="config-section__count">{{ Object.keys(section.settings).length }} settings</span>
          </summary>
          <div class="config-section__body">
            <div
              v-for="(value, key) in section.settings"
              :key="key"
              class="config-entry"
            >
              <span class="config-entry__key">{{ key }}</span>
              <span
                class="config-entry__value"
                :class="{ 'config-entry__value--masked': isMasked(value) }"
              >
                {{ formatValue(value) }}
              </span>
            </div>
          </div>
        </details>
      </div>
    </div>

    <div
      v-if="store.error"
      class="admin-error"
    >
      {{ store.error.userMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

const store = useAdminStore()

onMounted(() => {
  store.fetchConfig()
})

function formatSectionName(name: string): string {
  if (name === '_general') return 'General'
  return name.charAt(0).toUpperCase() + name.slice(1)
}

function isMasked(value: unknown): boolean {
  return value === '***MASKED***'
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
</script>

<style scoped>
.admin-section {
  margin-bottom: var(--space-l);
}

.config-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.config-section {
  border: 1px solid var(--clr-gray-800);
  border-radius: 6px;
}

.config-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-xs) var(--space-s);
  cursor: pointer;
  font-weight: 600;
}

.config-section__count {
  color: var(--clr-gray-500);
  font-size: var(--fs-300);
  font-weight: 400;
}

.config-section__body {
  padding: 0 var(--space-s) var(--space-s);
}

.config-entry {
  display: flex;
  gap: var(--space-m);
  padding: var(--space-3xs) 0;
  border-bottom: 1px solid var(--clr-gray-900);
}

.config-entry__key {
  min-width: 200px;
  color: var(--clr-gray-400);
  font-family: var(--ff-mono);
  font-size: var(--fs-300);
}

.config-entry__value {
  font-family: var(--ff-mono);
  font-size: var(--fs-300);
  word-break: break-all;
}

.config-entry__value--masked {
  color: var(--clr-gray-600);
  font-style: italic;
}

.admin-empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-xs) 0;
}

.admin-error {
  color: var(--clr-red-400, #f87171);
  padding: var(--space-xs);
  border: 1px solid var(--clr-red-800, #991b1b);
  border-radius: 4px;
  margin-top: var(--space-m);
}
</style>
