<template>
  <div>
    <div
      v-if="store.systemHealthLoading"
      class="grid__item"
    >
      <h2>Loading...</h2>
    </div>
    <template v-else-if="store.systemHealth">
      <!-- Server Info -->
      <div class="admin-section">
        <h2>Server</h2>
        <div class="admin-kv-list">
          <div class="admin-kv">
            <strong>Environment</strong>
            <span>{{ store.systemHealth.server.environment }}</span>
          </div>
          <div class="admin-kv">
            <strong>API URL</strong>
            <span>{{ store.systemHealth.server.api_url }}</span>
          </div>
          <div class="admin-kv">
            <strong>Server Time</strong>
            <span>{{ store.systemHealth.server.server_time }}</span>
          </div>
          <div class="admin-kv">
            <strong>Local Time</strong>
            <span>{{ localTime }}</span>
          </div>
        </div>
      </div>

      <!-- Docker Containers -->
      <div class="admin-section">
        <h2>Docker Containers</h2>
        <div
          v-if="store.systemHealth.docker.length === 0"
          class="admin__empty"
        >
          Docker status unavailable
        </div>
        <table
          v-else
          class="admin-table"
        >
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Image</th>
              <th>Started</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="container in store.systemHealth.docker"
              :key="container.name"
            >
              <td>{{ container.name }}</td>
              <td>
                <span :class="containerStatusClass(container.status)">
                  {{ container.status }}
                </span>
              </td>
              <td class="admin-table__mono">{{ container.image }}</td>
              <td>{{ formatDate(container.started_at, 'timestamp') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Database Stats -->
      <div class="admin-section">
        <h2>Database</h2>
        <div class="admin-kv-list admin-kv-list--inline">
          <div class="admin-kv">
            <strong>Size</strong>
            <span>{{ store.systemHealth.database.total_size_mb }} MB</span>
          </div>
          <div class="admin-kv">
            <strong>Active Connections</strong>
            <span>{{ store.systemHealth.database.active_connections }}</span>
          </div>
          <div class="admin-kv">
            <strong>Tables</strong>
            <span>{{ store.systemHealth.database.tables.length }}</span>
          </div>
        </div>
        <details class="admin-details">
          <summary>Table Row Counts</summary>
          <table class="admin-table admin-table--compact">
            <thead>
              <tr>
                <th>Schema</th>
                <th>Table</th>
                <th>Rows</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="table in store.systemHealth.database.tables"
                :key="`${table.schema_name}.${table.table_name}`"
              >
                <td class="admin-table__mono">{{ table.schema_name }}</td>
                <td class="admin-table__mono">{{ table.table_name }}</td>
                <td>{{ table.row_count.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </details>
      </div>

      <!-- Redis Stats -->
      <div class="admin-section">
        <h2>Redis</h2>
        <div class="admin-kv-list admin-kv-list--inline">
          <div class="admin-kv">
            <strong>Memory</strong>
            <span>{{ store.systemHealth.redis.memory_used_human }}</span>
          </div>
          <div class="admin-kv">
            <strong>Keys</strong>
            <span>{{ store.systemHealth.redis.key_count }}</span>
          </div>
          <div class="admin-kv">
            <strong>Clients</strong>
            <span>{{ store.systemHealth.redis.connected_clients }}</span>
          </div>
          <div class="admin-kv">
            <strong>Uptime</strong>
            <span>{{ formatUptime(store.systemHealth.redis.uptime_seconds) }}</span>
          </div>
        </div>
      </div>

      <!-- Disk Usage -->
      <div class="admin-section">
        <h2>Disk</h2>
        <div class="admin-kv-list admin-kv-list--inline">
          <div class="admin-kv">
            <strong>Used</strong>
            <span>{{ store.systemHealth.disk.used_gb }} / {{ store.systemHealth.disk.total_gb }} GB</span>
          </div>
          <div class="admin-kv">
            <strong>Free</strong>
            <span>{{ store.systemHealth.disk.free_gb }} GB</span>
          </div>
        </div>
        <div class="admin-meter">
          <div
            class="admin-meter__fill"
            :style="{ width: store.systemHealth.disk.percent_used + '%' }"
            :class="diskUsageClass"
          ></div>
          <span class="admin-meter__label">{{ store.systemHealth.disk.percent_used }}%</span>
        </div>
      </div>

      <!-- Recent Errors -->
      <div class="admin-section">
        <h2>
          Recent Errors
          <button
            class="button button--small"
            @click="store.fetchRecentErrors()"
          >
            Refresh
          </button>
        </h2>
        <div
          v-if="store.recentErrors.length === 0"
          class="admin__empty"
        >
          No recent errors
        </div>
        <table
          v-else
          class="admin-table admin-table--compact"
        >
          <thead>
            <tr>
              <th>Time</th>
              <th>Method</th>
              <th>Path</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Request ID</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(err, idx) in store.recentErrors"
              :key="idx"
            >
              <td>{{ formatDate(err.timestamp, 'timestamp') }}</td>
              <td>{{ err.method }}</td>
              <td class="admin-table__mono">{{ err.path }}</td>
              <td>
                <span :class="errorStatusClass(err.status)">{{ err.status }}</span>
              </td>
              <td>{{ err.duration_ms }}ms</td>
              <td class="admin-table__mono">{{ err.request_id }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div
      v-if="store.error"
      class="admin-error"
    >
      {{ store.error.userMessage }}
    </div>

    <div class="admin-actions">
      <label class="admin-auto-refresh">
        <input
          v-model="autoRefresh"
          type="checkbox"
        />
        Auto-refresh (30s)
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { formatDate } from '@/composables/formatDate'

const store = useAdminStore()

const autoRefresh = ref(false)
let refreshInterval: ReturnType<typeof setInterval> | null = null

const localTime = computed(() => new Date().toLocaleString())

onMounted(async () => {
  await Promise.all([store.fetchSystemHealth(), store.fetchRecentErrors()])
})

watch(autoRefresh, (enabled) => {
  if (enabled) {
    refreshInterval = setInterval(async () => {
      await Promise.all([store.fetchSystemHealth(), store.fetchRecentErrors()])
    }, 30000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  if (days > 0) return `${days}d ${hours}h`
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}

function containerStatusClass(status: string): string {
  if (status === 'running') return 'admin-status admin-status--ok'
  if (status === 'exited') return 'admin-status admin-status--error'
  return 'admin-status admin-status--warn'
}

function errorStatusClass(status: number): string {
  if (status >= 500) return 'admin-status admin-status--error'
  return 'admin-status admin-status--warn'
}

const diskUsageClass = computed(() => {
  if (!store.systemHealth) return ''
  const pct = store.systemHealth.disk.percent_used
  if (pct >= 90) return 'admin-meter__fill--danger'
  if (pct >= 75) return 'admin-meter__fill--warn'
  return 'admin-meter__fill--ok'
})
</script>

<style scoped>
.admin-meter {
  position: relative;
  height: 24px;
  background: var(--clr-gray-800);
  border-radius: 4px;
  margin-top: var(--space-2xs);
  overflow: hidden;
}

.admin-meter__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.admin-meter__fill--ok {
  background: var(--clr-green-600, #16a34a);
}

.admin-meter__fill--warn {
  background: var(--clr-yellow-600, #ca8a04);
}

.admin-meter__fill--danger {
  background: var(--clr-red-600, #dc2626);
}

.admin-meter__label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: var(--fs-300);
  font-weight: 600;
}

.admin-error {
  color: var(--clr-red-400, #f87171);
  padding: var(--space-xs);
  border: 1px solid var(--clr-red-800, #991b1b);
  border-radius: 4px;
  margin-top: var(--space-m);
}

.admin-details {
  margin-top: var(--space-xs);
}

.admin-details summary {
  cursor: pointer;
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
}

.admin-actions {
  margin-top: var(--space-m);
  display: flex;
  gap: var(--space-s);
}

.admin-auto-refresh {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  cursor: pointer;
}
</style>
