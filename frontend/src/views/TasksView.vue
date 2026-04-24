<template>
  <div>
    <TasksSubnav @add-task="showAddTask = true" />

    <!-- Info Bar (shown on priority, todo, search) -->
    <div
      v-if="activePage !== 'completed'"
      class="grid grid--one-column grid--tight"
    >
      <TaskInfoBar
        v-model:view-type="viewType"
        :total-count="store.totalCount"
      />
    </div>

    <!-- Priority Tasks (index page) -->
    <template v-if="activePage === 'priority'">
      <div class="grid grid--two-columns-wide grid--tight">
        <div :class="gridClass">
          <h2 class="task-layout__title">Priority Tasks</h2>
          <template v-if="viewType === 'block'">
            <TaskBlockPriority
              v-for="task in topTasks"
              :key="task.id"
              :task="task"
              @complete="onComplete"
            />
          </template>
          <template v-else>
            <TaskCompactPriority
              v-for="task in topTasks"
              :key="task.id"
              :task="task"
              @complete="onComplete"
              @delete="onDelete"
            />
          </template>
        </div>
        <div :class="gridClass">
          <h2 class="task-layout__title">Completed Today</h2>
          <template v-if="viewType === 'block'">
            <TaskBlockCompleted
              v-for="task in completedToday"
              :key="task.id"
              :task="task"
              @delete="onDelete"
            />
          </template>
          <template v-else>
            <TaskCompactCompleted
              v-for="task in completedToday"
              :key="task.id"
              :task="task"
              @delete="onDelete"
            />
          </template>
        </div>
      </div>
    </template>

    <!-- Outstanding Tasks (todo page) -->
    <template v-if="activePage === 'todo'">
      <div class="grid grid--one-column grid--tight">
        <div class="task-layout__filters">
          <h2 class="task-layout__title">Outstanding Tasks</h2>
          <NeuSelect
            v-model="selectedCategory"
            :options="categoryOptions"
            placeholder="All Categories"
            data-testid="todo-category-filter"
          />
        </div>
      </div>
      <div :class="gridClass">
        <draggable
          :list="filteredTodoTasks"
          item-key="id"
          handle=".task-drag-handle"
          data-testid="tasks-draggable"
          @end="onDragEnd"
        >
          <template #item="{ element: task }">
            <TaskBlockTodo
              v-if="viewType === 'block'"
              :task="task"
              @complete="onComplete"
              @shift="onShift"
              @delete="onDelete"
            />
            <TaskCompactTodo
              v-else
              :task="task"
              @complete="onComplete"
              @shift="onShift"
              @delete="onDelete"
            />
          </template>
        </draggable>
      </div>
    </template>

    <!-- Completed Tasks -->
    <template v-if="activePage === 'completed'">
      <div class="grid grid--one-column grid--tight">
        <TaskInfoBar
          v-model:view-type="viewType"
          :total-count="store.totalCount"
        />
        <h2 class="task-layout__title">Completed Tasks</h2>
        <div class="task-layout__filters">
          <NeuToggleGroup
            :model-value="selectedFilter"
            :options="dateFilterOptions"
            data-testid="completed-date-filter"
            @update:model-value="onFilterChange"
          />
          <NeuSelect
            v-model="selectedCategory"
            :options="categoryOptions"
            placeholder="All Categories"
            data-testid="completed-category-filter"
          />
        </div>
      </div>

      <template v-if="store.completedTasks.length > 0">
        <div class="grid grid--two-columns-wide grid--tight">
          <h3 class="task-layout__title">Total Tasks Completed: {{ filteredCompletedTasks.length }}</h3>
          <h3 class="task-layout__title">Average Completion Time: {{ avgCompletion }}</h3>

          <div :class="gridClass">
            <template v-if="viewType === 'block'">
              <TaskBlockCompleted
                v-for="task in filteredCompletedTasks"
                :key="task.id"
                :task="task"
                @delete="onDelete"
              />
            </template>
            <template v-else>
              <TaskCompactCompleted
                v-for="task in filteredCompletedTasks"
                :key="task.id"
                :task="task"
                @delete="onDelete"
              />
            </template>
          </div>

          <div class="grid grid--one-column-narrow-nested grid--tight">
            <CompletedChart :tasks="filteredCompletedTasks" />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="grid grid--one-column-wide grid--tight">
          <h3>{{ noCompletedMessage }}</h3>
        </div>
      </template>
    </template>

    <!-- Search Results -->
    <template v-if="activePage === 'search'">
      <div class="grid grid--one-column grid--tight">
        <h2 class="task-layout__title">Search Results</h2>
      </div>
      <div :class="gridClass">
        <template v-if="viewType === 'block'">
          <TaskBlockTodo
            v-for="task in store.sortedTasks"
            :key="task.id"
            :task="task"
            @complete="onComplete"
            @shift="onShift"
            @delete="onDelete"
          />
          <TaskBlockCompleted
            v-for="task in store.completedTasks"
            :key="task.id"
            :task="task"
            @delete="onDelete"
          />
        </template>
        <template v-else>
          <TaskCompactTodo
            v-for="task in store.sortedTasks"
            :key="task.id"
            :task="task"
            @complete="onComplete"
            @shift="onShift"
            @delete="onDelete"
          />
          <TaskCompactCompleted
            v-for="task in store.completedTasks"
            :key="task.id"
            :task="task"
            @delete="onDelete"
          />
        </template>
      </div>
    </template>

    <AddEditTaskModal
      :visible="showAddTask"
      @close="showAddTask = false"
      @create="onCreate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import draggable from 'vuedraggable'
import { useTasksStore, TASK_CATEGORIES } from '@/stores/tasks'
import type { CompletedTask } from '@/stores/tasks'
import type { Task } from '@/api/client'
import { useNotifications } from '@/composables/useNotifications'
import TasksSubnav from '@/components/tasks/TasksSubnav.vue'
import TaskInfoBar from '@/components/tasks/TaskInfoBar.vue'
import AddEditTaskModal from '@/components/tasks/AddEditTaskModal.vue'
import TaskBlockPriority from '@/components/tasks/TaskBlockPriority.vue'
import TaskCompactPriority from '@/components/tasks/TaskCompactPriority.vue'
import TaskBlockTodo from '@/components/tasks/TaskBlockTodo.vue'
import TaskCompactTodo from '@/components/tasks/TaskCompactTodo.vue'
import TaskBlockCompleted from '@/components/tasks/TaskBlockCompleted.vue'
import TaskCompactCompleted from '@/components/tasks/TaskCompactCompleted.vue'
import CompletedChart from '@/components/tasks/CompletedChart.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import NeuToggleGroup from '@/components/NeuToggleGroup.vue'
import type { NeuToggleGroupOption } from '@/components/NeuToggleGroup.vue'
import { DATE_FILTERS, dateFilterLabel, dateFilterRange, averageCompletionTime, type DateFilterKey } from '@/components/tasks/taskUtils'
import type { TaskCategory } from '@/api/client'

const route = useRoute()
const store = useTasksStore()
const { show } = useNotifications()

const viewType = ref<'block' | 'compact'>('block')
const selectedFilter = ref<DateFilterKey>('this_week')
const selectedCategory = ref<string>('')
const completedToday = ref<CompletedTask[]>([])
const showAddTask = ref(false)

const categoryOptions = [{ value: '', label: 'All Categories' }, ...TASK_CATEGORIES.map((c) => ({ value: c, label: c }))]

const dateFilterOptions: NeuToggleGroupOption<DateFilterKey>[] = DATE_FILTERS.map((f) => ({
  value: f,
  label: dateFilterLabel(f),
}))

const filteredTodoTasks = ref<Task[]>([])

function syncFilteredTodoTasks() {
  filteredTodoTasks.value = selectedCategory.value
    ? store.sortedTasks.filter((t) => t.category === selectedCategory.value)
    : [...store.sortedTasks]
}

watch(() => [store.sortedTasks, selectedCategory.value], syncFilteredTodoTasks, { deep: true, immediate: true })

const filteredCompletedTasks = computed(() => {
  if (!selectedCategory.value) return store.completedTasks
  return store.completedTasks.filter((t) => t.category === selectedCategory.value)
})

const activePage = computed<'priority' | 'todo' | 'completed' | 'search'>(() => {
  switch (route.name) {
    case 'tasks-todo':
      return 'todo'
    case 'tasks-completed':
      return 'completed'
    case 'tasks-search':
      return 'search'
    default:
      return 'priority'
  }
})

const gridClass = computed(() =>
  viewType.value === 'compact' ? 'grid grid--one-column-wide-nested grid--compact' : 'grid grid--one-column-narrow-nested grid--tight'
)

const topTasks = computed(() => store.sortedTasks.slice(0, 5))

const avgCompletion = computed(() => averageCompletionTime(filteredCompletedTasks.value))

const noCompletedMessage = computed(() => {
  const label = selectedFilter.value
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
  return `No completed tasks for time period: ${label}`
})

async function loadData() {
  try {
    if (activePage.value === 'priority') {
      await store.fetchTodo()
      const today = new Date()
      const todayStr = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString()
      const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1)
      const tomorrowStr = tomorrow.toISOString()
      await store.fetchCompleted(todayStr, tomorrowStr)
      completedToday.value = [...store.completedTasks]
      store.completedTasks = []
    } else if (activePage.value === 'todo') {
      await store.fetchTodo()
    } else if (activePage.value === 'completed') {
      await store.fetchTodo()
      const range = dateFilterRange(selectedFilter.value)
      await store.fetchCompleted(range.start, range.end)
    } else if (activePage.value === 'search') {
      const q = route.query.q as string
      if (q) {
        await store.search(q)
      }
    }
  } catch {
    show('Failed to load tasks', 'error')
  }
}

async function onComplete(id: number) {
  try {
    const completed = await store.complete(id)
    completedToday.value.unshift(completed)
    show(`${completed.name} completed`, 'success')
  } catch {
    show('Failed to complete task', 'error')
  }
}

async function onShift(id: number, positions: number) {
  const name = store.tasks.find((t) => t.id === id)?.name ?? 'Task'
  try {
    await store.shift(id, positions)
    const direction = positions >= 0 ? 'down' : 'up'
    show(`${name} shifted ${direction} ${Math.abs(positions)} positions`, 'success')
  } catch {
    show('Failed to shift task', 'error')
  }
}

async function onDelete(id: number) {
  const name = store.tasks.find((t) => t.id === id)?.name ?? 'Task'
  try {
    await store.remove(id)
    show(`${name} deleted`, 'success')
  } catch {
    show('Failed to delete task', 'error')
  }
}

async function onCreate(data: { name: string; category: TaskCategory; priority: number; notes?: string }) {
  try {
    await store.create(data)
    show(`${data.name} created`, 'success')
  } catch {
    show('Failed to create task', 'error')
  }
}

async function onDragEnd(evt: { oldIndex: number; newIndex: number }) {
  const { oldIndex, newIndex } = evt
  if (oldIndex === newIndex) return

  // After vuedraggable mutates filteredTodoTasks, the dragged task is at newIndex.
  // We pick a target priority based on the direction of travel:
  //   - Dragged UP: tie with the task immediately above (or priority 0 if at top).
  //   - Dragged DOWN: tie with the task immediately below (or prev-bottom's priority + 1 if at bottom).
  // This gives "approximate drag" — the tie is broken by add_date ASC at read time.
  const dragged = filteredTodoTasks.value[newIndex]
  if (!dragged) return

  let targetPriority: number
  if (oldIndex > newIndex) {
    const above = filteredTodoTasks.value[newIndex - 1]
    targetPriority = above ? above.priority : 0
  } else {
    const below = filteredTodoTasks.value[newIndex + 1]
    if (below) {
      targetPriority = below.priority
    } else {
      const prevBottom = filteredTodoTasks.value[newIndex - 1]
      targetPriority = prevBottom ? prevBottom.priority + 1 : 1
    }
  }

  try {
    await store.setPriority(dragged.id, targetPriority)
    syncFilteredTodoTasks()
  } catch {
    show('Failed to reorder task', 'error')
    // Roll back local drag by re-syncing from the store
    syncFilteredTodoTasks()
  }
}

function onFilterChange(filter: DateFilterKey) {
  selectedFilter.value = filter
  const range = dateFilterRange(filter)
  store.fetchCompleted(range.start, range.end)
}

watch(
  () => route.fullPath,
  () => {
    selectedCategory.value = ''
    loadData()
  }
)
onMounted(loadData)
</script>

<style scoped>
.task-layout__filters {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-s);
}
</style>
