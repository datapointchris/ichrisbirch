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
          class="admin__empty"
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
                <span>{{ formatDate(job.next_run_time, 'timestamp') }}</span>
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
                class="admin__empty"
              >
                Loading history...
              </div>
              <div
                v-else-if="filteredHistory(job.id).length === 0"
                class="admin__empty"
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
                    <td>{{ formatDate(run.started_at, 'timestamp') }}</td>
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
import { formatDate } from '@/composables/formatDate'

const store = useAdminStore()
const { show: notify } = useNotifications()
const expandedJob = ref<string | null>(null)

onMounted(() => {
  store.fetchSchedulerJobs()
})

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
</style>
