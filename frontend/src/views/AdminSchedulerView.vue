<template>
  <div>
    <div
      v-if="store.schedulerJobsLoading"
      class="grid__item"
    >
      <h2>Loading...</h2>
    </div>
    <template v-else>
      <!-- Job List -->
      <div class="admin-section">
        <h2>
          Scheduler Jobs
          <button
            class="button button--small"
            @click="store.fetchSchedulerJobs()"
          >
            Refresh
          </button>
        </h2>
        <div
          v-if="store.schedulerJobs.length === 0"
          class="admin-empty"
        >
          No scheduler jobs found
        </div>
        <div
          v-else
          class="scheduler-jobs"
        >
          <div
            v-for="job in store.schedulerJobs"
            :key="job.id"
            class="scheduler-job"
          >
            <div class="scheduler-job__header">
              <h3>{{ job.name }}</h3>
              <span
                v-if="job.is_paused"
                class="admin-status admin-status--warn"
                >Paused</span
              >
              <span
                v-else
                class="admin-status admin-status--ok"
                >Running</span
              >
            </div>
            <div class="scheduler-job__details">
              <div class="admin-kv">
                <strong>Trigger</strong>
                <span class="scheduler-job__mono">{{ job.trigger }}</span>
              </div>
              <div class="admin-kv">
                <strong>Next Run</strong>
                <span>{{ job.time_until_next_run }}</span>
              </div>
              <div
                v-if="job.next_run_time"
                class="admin-kv"
              >
                <strong>Next Run Time</strong>
                <span>{{ formatDateTime(job.next_run_time) }}</span>
              </div>
            </div>
            <div class="scheduler-job__actions">
              <button
                v-if="job.is_paused"
                class="button button--small"
                @click="handleResume(job.id, job.name)"
              >
                Resume
              </button>
              <button
                v-else
                class="button button--small"
                @click="handlePause(job.id, job.name)"
              >
                Pause
              </button>
              <button
                class="button button--small"
                @click="toggleHistory(job.id)"
              >
                {{ expandedJob === job.id ? 'Hide History' : 'Show History' }}
              </button>
              <button
                class="button button--small button--danger"
                @click="handleDelete(job.id, job.name)"
              >
                <span class="button__text button__text--danger">Delete</span>
              </button>
            </div>

            <!-- Expandable Run History -->
            <div
              v-if="expandedJob === job.id"
              class="scheduler-job__history"
            >
              <div
                v-if="store.jobHistoryLoading"
                class="admin-empty"
              >
                Loading history...
              </div>
              <div
                v-else-if="filteredHistory(job.id).length === 0"
                class="admin-empty"
              >
                No run history
              </div>
              <table
                v-else
                class="admin-table admin-table--compact"
              >
                <thead>
                  <tr>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Result</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="run in filteredHistory(job.id)"
                    :key="run.id"
                  >
                    <td>{{ formatDateTime(run.started_at) }}</td>
                    <td>{{ run.duration_seconds.toFixed(2) }}s</td>
                    <td>
                      <span :class="run.success ? 'admin-status admin-status--ok' : 'admin-status admin-status--error'">
                        {{ run.success ? 'Success' : 'Failed' }}
                      </span>
                    </td>
                    <td>
                      <span
                        v-if="run.error_message"
                        class="scheduler-job__mono"
                        >{{ run.error_type }}: {{ run.error_message }}</span
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="store.error"
      class="admin-error"
    >
      {{ store.error.userMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'

const store = useAdminStore()
const { show: notify } = useNotifications()
const expandedJob = ref<string | null>(null)

onMounted(() => {
  store.fetchSchedulerJobs()
})

function formatDateTime(iso: string | null): string {
  if (!iso) return 'N/A'
  return new Date(iso).toLocaleString()
}

function filteredHistory(jobId: string) {
  return store.jobHistory.filter((r) => r.job_id === jobId)
}

async function toggleHistory(jobId: string) {
  if (expandedJob.value === jobId) {
    expandedJob.value = null
    return
  }
  expandedJob.value = jobId
  await store.fetchJobHistory(jobId)
}

async function handlePause(jobId: string, name: string) {
  try {
    await store.pauseJob(jobId)
    notify(`Paused: ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to pause ${name}: ${detail}`, 'error')
  }
}

async function handleResume(jobId: string, name: string) {
  try {
    await store.resumeJob(jobId)
    notify(`Resumed: ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to resume ${name}: ${detail}`, 'error')
  }
}

async function handleDelete(jobId: string, name: string) {
  if (!confirm(`Delete scheduler job "${name}"? This cannot be undone.`)) return
  try {
    await store.deleteJob(jobId)
    notify(`Deleted: ${name}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete ${name}: ${detail}`, 'error')
  }
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

.scheduler-jobs {
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
}

.scheduler-job {
  border: 1px solid var(--clr-gray-800);
  border-radius: 6px;
  padding: var(--space-s);
}

.scheduler-job__header {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  margin-bottom: var(--space-xs);
}

.scheduler-job__header h3 {
  margin: 0;
}

.scheduler-job__details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-m);
  margin-bottom: var(--space-xs);
}

.scheduler-job__actions {
  display: flex;
  gap: var(--space-2xs);
}

.scheduler-job__history {
  margin-top: var(--space-s);
  padding-top: var(--space-s);
  border-top: 1px solid var(--clr-gray-800);
}

.scheduler-job__mono {
  font-family: var(--ff-mono);
  font-size: var(--fs-300);
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

.admin-status--warn {
  color: var(--clr-yellow-300, #fde047);
  background: var(--clr-yellow-900, #713f12);
}

.admin-status--error {
  color: var(--clr-red-300, #fca5a5);
  background: var(--clr-red-900, #7f1d1d);
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
