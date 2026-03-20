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
            <strong>Result</strong>
            <span :class="store.smokeReport.all_passed ? 'admin-status admin-status--ok' : 'admin-status admin-status--error'">
              {{ store.smokeReport.all_passed ? 'All Passed' : 'FAILURES' }}
            </span>
          </div>
          <div class="admin-kv">
            <strong>Run At</strong>
            <span>{{ formatDateTime(store.smokeReport.run_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Results -->
      <div class="admin-section">
        <table class="admin-table admin-table--compact">
          <thead>
            <tr>
              <th>Result</th>
              <th>Status</th>
              <th>Path</th>
              <th>Name</th>
              <th>Time</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="result in store.smokeReport.results"
              :key="result.path"
            >
              <td>
                <span :class="result.passed ? 'admin-status admin-status--ok' : 'admin-status admin-status--error'">
                  {{ result.passed ? 'PASS' : 'FAIL' }}
                </span>
              </td>
              <td>{{ result.status_code ?? '—' }}</td>
              <td class="admin-table__mono">{{ result.path }}</td>
              <td>{{ result.name }}</td>
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

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>
