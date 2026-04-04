<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="autofun-tabs">
      <button
        class="autofun-tabs__tab"
        :class="{ 'autofun-tabs__tab--active': activeTab === 'list' }"
        data-testid="autofun-tab-list"
        @click="activeTab = 'list'"
      >
        <i class="fa-solid fa-list-ul"></i>
        Fun List
      </button>
      <button
        class="autofun-tabs__tab"
        :class="{ 'autofun-tabs__tab--active': activeTab === 'scheduler' }"
        data-testid="autofun-tab-scheduler"
        @click="activeTab = 'scheduler'"
      >
        <i class="fa-solid fa-calendar-days"></i>
        Scheduler
      </button>
    </div>

    <!-- Fun List Tab -->
    <div v-if="activeTab === 'list'">
      <div class="add-item-wrapper">
        <button
          class="button"
          data-testid="autofun-add-button"
          @click="showModal = true"
        >
          <span class="button__text">Add Activity</span>
        </button>
        <label class="autofun-toggle">
          <input
            v-model="showCompleted"
            type="checkbox"
            data-testid="autofun-show-completed"
          />
          Show completed
        </label>
      </div>

      <div
        v-if="store.loading"
        class="grid__item"
      >
        <h2>Loading...</h2>
      </div>
      <template v-else>
        <div class="autofun-list">
          <div
            v-for="item in displayedItems"
            :key="item.id"
            class="autofun-list__item"
            :class="{ 'autofun-list__item--completed': item.is_completed }"
            data-testid="autofun-item"
          >
            <div class="autofun-list__item-content">
              <span
                class="autofun-list__item-name"
                :class="{ 'autofun-list__item-name--completed': item.is_completed }"
                >{{ item.name }}</span
              >
              <span
                v-if="item.notes"
                class="autofun-list__item-notes"
                >{{ item.notes }}</span
              >
              <span
                v-if="item.is_completed && item.completed_date"
                class="autofun-list__item-completed-date"
                >Completed {{ formatDate(item.completed_date, 'shortDate') }}</span
              >
            </div>
            <div
              v-if="!item.is_completed"
              class="autofun-list__item-actions"
            >
              <button
                class="button"
                data-testid="autofun-edit-button"
                @click="openEdit(item)"
              >
                <span class="button__text">Edit</span>
              </button>
              <button
                class="button button--danger"
                data-testid="autofun-delete-button"
                @click="handleDelete(item.id)"
              >
                <span class="button__text button__text--danger">Delete</span>
              </button>
            </div>
          </div>
          <div
            v-if="displayedItems.length === 0"
            class="autofun-list__empty"
          >
            {{ showCompleted ? 'No activities yet.' : 'No active activities. Add some!' }}
          </div>
        </div>
      </template>
    </div>

    <!-- Scheduler Tab -->
    <div v-if="activeTab === 'scheduler'">
      <div class="autofun-scheduler">
        <h2>Scheduler Settings</h2>

        <div class="autofun-scheduler__status">
          <span
            class="autofun-scheduler__status-indicator"
            :class="
              schedulerPrefs.is_paused ? 'autofun-scheduler__status-indicator--paused' : 'autofun-scheduler__status-indicator--active'
            "
          >
            {{ schedulerPrefs.is_paused ? 'Paused' : 'Active' }}
          </span>
        </div>

        <form
          class="autofun-scheduler__form"
          @submit.prevent="saveSchedulerSettings"
        >
          <div class="add-edit-modal__form-row">
            <div class="add-edit-modal__form-item">
              <label for="autofun-interval">Interval (days)</label>
              <input
                id="autofun-interval"
                v-model.number="schedulerPrefs.interval_days"
                data-testid="autofun-interval-input"
                type="number"
                min="1"
                class="textbox add-edit-modal__number-input"
              />
            </div>
            <div class="add-edit-modal__form-item">
              <label for="autofun-concurrent">Max on task list</label>
              <input
                id="autofun-concurrent"
                v-model.number="schedulerPrefs.max_concurrent"
                data-testid="autofun-concurrent-input"
                type="number"
                min="1"
                class="textbox add-edit-modal__number-input"
              />
            </div>
            <div class="add-edit-modal__form-item">
              <label for="autofun-priority">Task priority</label>
              <input
                id="autofun-priority"
                v-model.number="schedulerPrefs.task_priority"
                data-testid="autofun-priority-input"
                type="number"
                min="1"
                class="textbox add-edit-modal__number-input"
              />
            </div>
          </div>

          <label class="autofun-toggle autofun-scheduler__pause-toggle">
            <input
              v-model="schedulerPrefs.is_paused"
              type="checkbox"
              data-testid="autofun-paused-input"
            />
            Pause scheduler
          </label>

          <div class="add-edit-modal__form-buttons">
            <button
              type="submit"
              class="button"
              data-testid="autofun-save-settings-button"
            >
              <span class="button__text">Save Settings</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <AddEditAutoFunModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useAutoFunStore } from '@/stores/autofun'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { AutoFun, AutoFunCreate, AutoFunUpdate, AutoFunPreferences } from '@/api/types'
import AddEditAutoFunModal from '@/components/autofun/AddEditAutoFunModal.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { AUTOFUN_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = AUTOFUN_SUBNAV
import { formatDate } from '@/composables/formatDate'

const store = useAutoFunStore()
const auth = useAuthStore()
const { show: notify } = useNotifications()

const activeTab = ref<'list' | 'scheduler'>('list')
const showModal = ref(false)
const editTarget = ref<AutoFun | null>(null)
const showCompleted = ref(false)

const schedulerPrefs = reactive<AutoFunPreferences>({
  interval_days: 7,
  max_concurrent: 1,
  is_paused: false,
  task_priority: 7,
})

const displayedItems = computed(() => (showCompleted.value ? [...store.activeItems, ...store.completedItems] : store.activeItems))

onMounted(async () => {
  await store.fetchAll()
  const saved = auth.preferences?.autofun as AutoFunPreferences | undefined
  if (saved) {
    schedulerPrefs.interval_days = saved.interval_days ?? 7
    schedulerPrefs.max_concurrent = saved.max_concurrent ?? 1
    schedulerPrefs.is_paused = saved.is_paused ?? false
    schedulerPrefs.task_priority = saved.task_priority ?? 7
  }
})

function openEdit(item: AutoFun) {
  editTarget.value = item
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: AutoFunCreate) {
  try {
    await store.create(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add activity: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: AutoFunUpdate) {
  const name = store.items.find((i) => i.id === id)?.name ?? 'Activity'
  try {
    await store.update(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update activity: ${detail}`, 'error')
  }
}

async function handleDelete(id: number) {
  const name = store.items.find((i) => i.id === id)?.name ?? 'Activity'
  try {
    await store.remove(id)
    notify(`${name} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete activity: ${detail}`, 'error')
  }
}

async function saveSchedulerSettings() {
  try {
    await auth.updatePreferences({ autofun: { ...schedulerPrefs } })
    notify('Scheduler settings saved', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to save settings: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.autofun-tabs {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
  margin-bottom: var(--space-m);
}

.autofun-tabs__tab {
  background: none;
  border: none;
  color: var(--clr-gray-400);
  font-size: var(--fs-400);
  padding: var(--space-3xs) var(--space-xs);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  transition: color 0.2s;
}

.autofun-tabs__tab:hover {
  color: var(--clr-text);
}

.autofun-tabs__tab--active {
  color: var(--clr-accent);
  border-bottom: 2px solid var(--clr-accent);
  margin-bottom: -2px;
}

.autofun-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-s);
  margin-top: var(--space-m);
}

.autofun-list__item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-s) var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  gap: var(--space-m);
}

.autofun-list__item--completed {
  opacity: 0.6;
}

.autofun-list__item-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
}

.autofun-list__item-name {
  font-size: var(--fs-500);
}

.autofun-list__item-name--completed {
  text-decoration: line-through;
  color: var(--clr-gray-400);
}

.autofun-list__item-notes {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
}

.autofun-list__item-completed-date {
  font-size: var(--fs-200);
  color: var(--clr-gray-500);
  font-style: italic;
}

.autofun-list__item-actions {
  display: flex;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.autofun-list__empty {
  color: var(--clr-gray-500);
  font-style: italic;
}

.autofun-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  cursor: pointer;
}

.autofun-scheduler {
  max-width: 600px;
  margin-top: var(--space-m);
}

.autofun-scheduler__status {
  margin-bottom: var(--space-m);
}

.autofun-scheduler__status-indicator {
  font-size: var(--fs-300);
  padding: var(--space-3xs) var(--space-xs);
  border-radius: var(--border-radius);
}

.autofun-scheduler__status-indicator--active {
  background: color-mix(in oklch, var(--clr-success) 20%, transparent);
  color: var(--clr-success);
}

.autofun-scheduler__status-indicator--paused {
  background: color-mix(in oklch, var(--clr-warning) 20%, transparent);
  color: var(--clr-warning);
}

.autofun-scheduler__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
}

.autofun-scheduler__pause-toggle {
  margin-top: var(--space-xs);
}
</style>
