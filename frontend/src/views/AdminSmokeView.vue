<template>
  <div>
    <div class="admin-section">
      <h2>
        Smoke Tests
        <button
          class="button button--small"
          :disabled="store.smokeTestsRunning"
          @click="store.runSmokeTests()"
        >
          {{ store.smokeTestsRunning ? 'Running...' : 'Run Smoke Tests' }}
        </button>
      </h2>
    </div>

    <template v-if="store.smokeReport">
      <!-- Summary -->
      <div class="admin-section">
        <div class="admin-kv-list admin-kv-list--inline">
          <div class="admin-kv">
            <strong>Environment</strong>
            <span>{{ store.smokeReport.environment }}</span>
          </div>
          <div class="admin-kv">
            <strong>Total</strong>
            <span>{{ store.smokeReport.total }}</span>
          </div>
          <div class="admin-kv">
            <strong>Passed</strong>
            <span class="admin-status admin-status--ok">{{ store.smokeReport.passed }}</span>
          </div>
          <div class="admin-kv">
            <strong>Failed</strong>
            <span :class="store.smokeReport.failed > 0 ? 'admin-status admin-status--error' : 'admin-status admin-status--ok'">
              {{ store.smokeReport.failed }}
            </span>
          </div>
          <div class="admin-kv">
            <strong>Duration</strong>
            <span>{{ store.smokeReport.duration_ms }}ms</span>
          </div>
          <div class="admin-kv">
            <strong>Critical</strong>
            <span :class="store.smokeReport.all_critical_passed ? 'admin-status admin-status--ok' : 'admin-status admin-status--error'">
              {{ store.smokeReport.all_critical_passed ? 'All Passed' : 'FAILURES' }}
            </span>
          </div>
          <div class="admin-kv">
            <strong>Run At</strong>
            <span>{{ formatDateTime(store.smokeReport.run_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Results by category -->
      <div
        v-for="category in categories"
        :key="category"
        class="admin-section"
      >
        <h2>{{ categoryLabel(category) }}</h2>
        <table class="admin-table admin-table--compact">
          <thead>
            <tr>
              <th>Result</th>
              <th>Name</th>
              <th>Path</th>
              <th>Status</th>
              <th>Time</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="result in resultsByCategory(category)"
              :key="result.path"
            >
              <td>
                <span :class="result.passed ? 'admin-status admin-status--ok' : 'admin-status admin-status--error'">
                  {{ result.passed ? 'PASS' : 'FAIL' }}
                </span>
              </td>
              <td>{{ result.name }}</td>
              <td class="admin-table__mono">{{ result.path }}</td>
              <td>{{ result.status_code ?? '—' }}</td>
              <td>{{ result.response_time_ms }}ms</td>
              <td class="admin-table__mono">{{ result.error ?? '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div
      v-else-if="!store.smokeTestsRunning"
      class="admin-empty"
    >
      Click "Run Smoke Tests" to check all endpoints
    </div>

    <div
      v-if="store.smokeTestsRunning"
      class="admin-empty"
    >
      Running smoke tests against all endpoints...
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
import { useAdminStore } from '@/stores/admin'

const store = useAdminStore()

const categories = ['critical', 'important', 'secondary']

function categoryLabel(category: string): string {
  return category.charAt(0).toUpperCase() + category.slice(1)
}

function resultsByCategory(category: string) {
  if (!store.smokeReport) return []
  return store.smokeReport.results.filter((r) => r.category === category)
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>

<style scoped>
.admin-section {
  margin-bottom: var(--space-l);
}

.admin-section h2 {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  margin-bottom: var(--space-xs);
}

.admin-kv-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
}

.admin-kv-list--inline {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--space-m);
}

.admin-kv {
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
}

.admin-kv strong {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table th,
.admin-table td {
  text-align: left;
  padding: var(--space-3xs) var(--space-xs);
  border-bottom: 1px solid var(--clr-gray-800);
}

.admin-table th {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.admin-table--compact th,
.admin-table--compact td {
  padding: var(--space-3xs) var(--space-2xs);
  font-size: var(--fs-300);
}

.admin-table__mono {
  font-family: var(--ff-mono);
  font-size: var(--fs-300);
}

.admin-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: var(--fs-300);
  font-weight: 600;
}

.admin-status--ok {
  color: var(--clr-green-300, #86efac);
  background: var(--clr-green-900, #14532d);
}

.admin-status--error {
  color: var(--clr-red-300, #fca5a5);
  background: var(--clr-red-900, #7f1d1d);
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

.button--small {
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-300);
}
</style>
