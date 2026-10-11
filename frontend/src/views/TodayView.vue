<template>
  <div
    class="today"
    data-testid="today-page"
  >
    <section
      class="today-add"
      data-testid="today-add"
    >
      <div
        class="today-modes"
        role="radiogroup"
        aria-label="Add to"
      >
        <button
          v-for="choice in ADD_MODES"
          :key="choice.mode"
          type="button"
          role="radio"
          class="today-modes__chip"
          :class="{ 'today-modes__chip--on': mode === choice.mode }"
          :aria-checked="mode === choice.mode"
          :data-testid="`today-mode-${choice.mode}`"
          @click="chooseMode(choice.mode)"
        >
          {{ choice.label }}
        </button>
      </div>
      <form
        class="today-add__form"
        @submit.prevent="add"
      >
        <input
          ref="addInput"
          v-model="typed"
          type="text"
          class="textbox today-add__input"
          data-testid="today-add-input"
          :placeholder="mode === 'task' ? 'Add a task…' : 'Add to shopping…'"
          :aria-label="mode === 'task' ? 'Add a task' : 'Add to shopping'"
          autocomplete="off"
          enterkeyhint="done"
        />
        <button
          type="submit"
          class="today-add__submit"
          data-testid="today-add-submit"
          aria-label="Add"
        >
          <i class="fa-solid fa-plus"></i>
        </button>
      </form>
      <div
        v-if="mode === 'task'"
        ref="categoryRow"
        class="today-categories"
        role="radiogroup"
        aria-label="Category"
        data-testid="today-categories"
      >
        <button
          v-for="choice in TASK_CATEGORIES"
          :key="choice"
          type="button"
          role="radio"
          class="today-categories__chip"
          :class="{ 'today-categories__chip--on': category === choice }"
          :aria-checked="category === choice"
          data-testid="today-category"
          @click="chooseCategory(choice)"
        >
          {{ choice }}
        </button>
      </div>
      <p
        v-if="addNote"
        class="today-add__note"
        data-testid="today-add-note"
      >
        {{ addNote }}
      </p>
    </section>

    <section
      class="today-block"
      data-testid="today-tasks"
    >
      <RouterLink
        to="/tasks"
        class="today-block__header"
      >
        <h2 class="today-block__title">Tasks</h2>
        <span
          v-if="store.status.tasks === 'loaded'"
          class="today-block__count"
        >
          {{ store.openTaskCount }} open
        </span>
        <i class="fa-solid fa-chevron-right"></i>
      </RouterLink>
      <p
        v-if="store.status.tasks !== 'loaded'"
        class="today-block__empty"
        data-testid="today-tasks-state"
      >
        {{ notLoaded('tasks') }}
      </p>
      <p
        v-else-if="store.openTasks.length === 0"
        class="today-block__empty"
      >
        Nothing open
      </p>
      <ul
        v-else
        class="today-block__rows"
      >
        <li
          v-for="task in store.openTasks"
          :key="task.id"
          class="today-row"
          :class="{ 'today-row--checking': checking.has(taskKey(task)) }"
          data-testid="today-task"
        >
          <button
            type="button"
            class="today-row__check"
            data-testid="today-task-complete"
            :aria-label="`Complete ${task.name}`"
            :disabled="checking.has(taskKey(task))"
            @click="completeTask(task)"
          >
            <i class="fa-solid fa-check"></i>
          </button>
          <span class="today-row__name">{{ task.name }}</span>
          <span class="today-row__tag">{{ task.category }}</span>
        </li>
      </ul>
      <template v-if="store.status.tasks === 'loaded' && store.doneTasks.length">
        <h3 class="today-block__subtitle">Done today</h3>
        <ul class="today-block__rows">
          <li
            v-for="task in store.doneTasks"
            :key="task.id"
          >
            <button
              type="button"
              class="today-done"
              data-testid="today-task-done"
              :aria-label="`Reopen ${task.name}`"
              @click="reopenTask(task)"
            >
              <i class="fa-solid fa-rotate-left"></i>
              <span class="today-done__name">{{ task.name }}</span>
            </button>
          </li>
        </ul>
      </template>
    </section>

    <section
      class="today-block"
      data-testid="today-habits"
    >
      <RouterLink
        to="/habits"
        class="today-block__header"
      >
        <h2 class="today-block__title">Habits</h2>
        <span
          v-if="store.status.habits === 'loaded'"
          class="today-block__count"
        >
          {{ store.habitsLeft }} left
        </span>
        <i class="fa-solid fa-chevron-right"></i>
      </RouterLink>
      <p
        v-if="store.status.habits !== 'loaded'"
        class="today-block__empty"
        data-testid="today-habits-state"
      >
        {{ notLoaded('habits') }}
      </p>
      <p
        v-else-if="store.habitsLeft === 0"
        class="today-block__empty"
      >
        {{ store.habitsDone.length ? 'All done for today' : 'No habits due' }}
      </p>
      <template
        v-for="(habits, categoryName) in habitsShown"
        :key="categoryName"
      >
        <h3 class="today-block__subtitle">{{ categoryName }}</h3>
        <ul class="today-block__rows">
          <li
            v-for="habit in habits"
            :key="habit.id"
            class="today-row"
            :class="{ 'today-row--checking': checking.has(habitKey(habit)) }"
            data-testid="today-habit"
          >
            <button
              type="button"
              class="today-row__check"
              data-testid="today-habit-check"
              :aria-label="`Done ${habit.name}`"
              :disabled="checking.has(habitKey(habit))"
              @click="checkHabit(habit)"
            >
              <i class="fa-solid fa-check"></i>
            </button>
            <span class="today-row__name">{{ habit.name }}</span>
          </li>
        </ul>
      </template>
      <template v-if="store.status.habits === 'loaded' && store.habitsDone.length">
        <h3 class="today-block__subtitle">Done today</h3>
        <ul class="today-block__rows">
          <li
            v-for="completion in store.habitsDone"
            :key="completion.id"
          >
            <button
              type="button"
              class="today-done"
              data-testid="today-habit-done"
              :aria-label="`Undo ${completion.name}`"
              @click="uncheckHabit(completion)"
            >
              <i class="fa-solid fa-rotate-left"></i>
              <span class="today-done__name">{{ completion.name }}</span>
            </button>
          </li>
        </ul>
      </template>
    </section>

    <section
      class="today-block"
      data-testid="today-shopping"
    >
      <RouterLink
        to="/shopping"
        class="today-block__header"
      >
        <h2 class="today-block__title">Shopping</h2>
        <span
          class="today-block__count"
          data-testid="today-shopping-count"
        >
          {{ store.status.shopping === 'loaded' ? `${store.shoppingCount} on the list` : notLoaded('shopping') }}
        </span>
        <i class="fa-solid fa-chevron-right"></i>
      </RouterLink>
    </section>

    <section
      class="today-block"
      data-testid="today-coming-up"
    >
      <div class="today-block__header">
        <h2 class="today-block__title">Coming up</h2>
      </div>
      <p
        v-if="comingUpLoading"
        class="today-block__empty"
        data-testid="today-coming-up-state"
      >
        {{ LOADING }}
      </p>
      <template v-else>
        <ul
          v-if="store.comingUpRows.length"
          class="today-block__rows"
        >
          <li
            v-for="row in store.comingUpRows"
            :key="`${row.kind}-${row.id}`"
          >
            <RouterLink
              :to="row.kind === 'countdown' ? '/countdowns' : '/events'"
              class="today-ahead"
              :data-testid="`today-${row.kind}`"
            >
              <i
                class="fa-solid today-ahead__icon"
                :class="row.kind === 'countdown' ? 'fa-hourglass-half' : 'fa-calendar'"
              ></i>
              <span class="today-ahead__name">{{ row.name }}</span>
              <i
                v-if="row.attending"
                class="fa-solid fa-check today-ahead__going"
                aria-label="Going"
              ></i>
              <span class="today-ahead__when">{{ daysUntil(row.day, store.today) }}</span>
            </RouterLink>
          </li>
        </ul>
        <p
          v-if="comingUpFailed.length"
          class="today-block__empty"
          data-testid="today-coming-up-state"
        >
          Could not load {{ comingUpFailed.join(' or ') }}
        </p>
        <p
          v-else-if="store.comingUpRows.length === 0"
          class="today-block__empty"
        >
          Nothing coming up
        </p>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ApiError } from '@/api/errors'
import type { Habit, HabitCompleted, Task, TaskCategory } from '@/api/client'
import { useNotifications } from '@/composables/useNotifications'
import type { CompletedTask } from '@/stores/tasks'
import { TASK_CATEGORIES } from '@/stores/tasks'
import { type TodayPart, daysUntil, useTodayStore } from '@/stores/today'

type AddMode = 'task' | 'shopping'

const ADD_MODES: { mode: AddMode; label: string }[] = [
  { mode: 'task', label: 'Task' },
  { mode: 'shopping', label: 'Shopping' },
]
const MODE_STORAGE_KEY = 'today-add-mode'
const CATEGORY_STORAGE_KEY = 'today-task-category'
const PICK_CATEGORY = 'Pick a category for the task'
// Long enough to see the check land before the row leaves.
const CHECK_OFF_DELAY_MS = 300
// How often a page left visible checks whether midnight has passed, as /habits does.
const ROLLOVER_POLL_MS = 60_000
const LOADING = 'Loading…'

const store = useTodayStore()
const { show: notify } = useNotifications()

function notLoaded(part: TodayPart): string {
  return store.status[part] === 'failed' ? `Could not load ${part}` : LOADING
}

const habitsShown = computed(() => (store.status.habits === 'loaded' ? store.habitsDue : {}))
const comingUpLoading = computed(() => store.status.countdowns === 'loading' || store.status.events === 'loading')
const comingUpFailed = computed(() => (['countdowns', 'events'] as const).filter((part) => store.status[part] === 'failed'))

const addInput = ref<HTMLInputElement | null>(null)
const categoryRow = ref<HTMLElement | null>(null)
const typed = ref('')
const addNote = ref('')
const checking = ref(new Set<string>())

function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStored(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // A private window refuses storage; the choice then lasts until the page closes.
  }
}

function storedMode(): AddMode {
  return readStored(MODE_STORAGE_KEY) === 'shopping' ? 'shopping' : 'task'
}

function storedCategory(): TaskCategory | null {
  const saved = readStored(CATEGORY_STORAGE_KEY)
  return TASK_CATEGORIES.find((choice) => choice === saved) ?? null
}

const mode = ref<AddMode>(storedMode())
const category = ref<TaskCategory | null>(storedCategory())

function chooseMode(next: AddMode) {
  mode.value = next
  addNote.value = ''
  writeStored(MODE_STORAGE_KEY, next)
}

function chooseCategory(next: TaskCategory) {
  category.value = next
  if (addNote.value === PICK_CATEGORY) addNote.value = ''
  writeStored(CATEGORY_STORAGE_KEY, next)
}

function failure(action: string, e: unknown) {
  const detail = e instanceof ApiError ? e.userMessage : String(e)
  notify(`Could not ${action}: ${detail}`, 'error')
}

async function add() {
  const name = typed.value.trim()
  if (!name) return
  if (mode.value === 'task' && !category.value) {
    addNote.value = PICK_CATEGORY
    return
  }
  typed.value = ''
  addInput.value?.focus()
  try {
    if (mode.value === 'task' && category.value) {
      const task = await store.addTask(name, category.value)
      addNote.value = `${task.name} → ${task.category}`
    } else {
      const item = await store.addShoppingItem(name)
      addNote.value = `${item.name} → ${item.section_name ?? 'Unsorted'}`
    }
  } catch (e) {
    typed.value = name
    failure(`add ${name}`, e)
  }
}

function taskKey(task: Task): string {
  return `task-${task.id}`
}

function habitKey(habit: Habit): string {
  return `habit-${habit.id}`
}

async function checkOff(key: string, action: string, write: () => Promise<void>) {
  if (checking.value.has(key)) return
  checking.value.add(key)
  await new Promise((resolve) => setTimeout(resolve, CHECK_OFF_DELAY_MS))
  try {
    await write()
  } catch (e) {
    failure(action, e)
  } finally {
    checking.value.delete(key)
  }
}

async function completeTask(task: Task) {
  await checkOff(taskKey(task), `complete ${task.name}`, () => store.completeTask(task))
}

async function checkHabit(habit: Habit) {
  await checkOff(habitKey(habit), `check off ${habit.name}`, () => store.checkHabit(habit))
}

async function reopenTask(task: CompletedTask) {
  try {
    await store.reopenTask(task)
  } catch (e) {
    failure(`reopen ${task.name}`, e)
  }
}

async function uncheckHabit(completion: HabitCompleted) {
  try {
    await store.uncheckHabit(completion)
  } catch (e) {
    failure(`undo ${completion.name}`, e)
  }
}

function reportFailed(failed: TodayPart[]) {
  if (failed.length) notify(`Could not load ${failed.join(', ')}`, 'error')
}

async function load() {
  reportFailed(await store.load())
}

// An installed app resumes where it was left and has no reload control, and
// the lists may have changed from another device meanwhile, so every return
// reloads them.
function onVisible() {
  if (document.visibilityState === 'visible') void load()
}

// A tab that never goes hidden fires no visibility change at midnight.
let rolloverTimer: ReturnType<typeof setInterval> | undefined

onMounted(async () => {
  document.addEventListener('visibilitychange', onVisible)
  rolloverTimer = setInterval(() => void store.syncDay().then(reportFailed), ROLLOVER_POLL_MS)
  // The category row scrolls sideways on a phone, so the remembered choice is brought into view.
  await nextTick()
  categoryRow.value?.querySelector('.today-categories__chip--on')?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' })
  await load()
})

onUnmounted(() => {
  clearInterval(rolloverTimer)
  document.removeEventListener('visibilitychange', onVisible)
})
</script>
