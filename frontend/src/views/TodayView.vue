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
        <span class="today-block__count">{{ store.openTaskCount }} open</span>
        <i class="fa-solid fa-chevron-right"></i>
      </RouterLink>
      <p
        v-if="store.openTasks.length === 0"
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
      <template v-if="store.doneTasks.length">
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
        <span class="today-block__count">{{ store.habitsLeft }} left</span>
        <i class="fa-solid fa-chevron-right"></i>
      </RouterLink>
      <p
        v-if="store.habitsLeft === 0"
        class="today-block__empty"
      >
        {{ store.habitsDone.length ? 'All done for today' : 'No habits due' }}
      </p>
      <template
        v-for="(habits, categoryName) in store.habitsDue"
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
      <template v-if="store.habitsDone.length">
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
        <span class="today-block__count">{{ store.shoppingCount }} on the list</span>
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
        v-if="store.countdownsComing.length === 0 && store.eventsComing.length === 0"
        class="today-block__empty"
      >
        Nothing coming up
      </p>
      <ul class="today-block__rows">
        <li
          v-for="countdown in store.countdownsComing"
          :key="`countdown-${countdown.id}`"
        >
          <RouterLink
            to="/countdowns"
            class="today-ahead"
            data-testid="today-countdown"
          >
            <i class="fa-solid fa-hourglass-half today-ahead__icon"></i>
            <span class="today-ahead__name">{{ countdown.name }}</span>
            <span class="today-ahead__when">{{ daysUntil(countdown.due_date, store.today) }}</span>
          </RouterLink>
        </li>
        <li
          v-for="event in store.eventsComing"
          :key="`event-${event.id}`"
        >
          <RouterLink
            to="/events"
            class="today-ahead"
            data-testid="today-event"
          >
            <i class="fa-solid fa-calendar today-ahead__icon"></i>
            <span class="today-ahead__name">{{ event.name }}</span>
            <i
              v-if="event.attending"
              class="fa-solid fa-check today-ahead__going"
              aria-label="Going"
            ></i>
            <span class="today-ahead__when">{{ formatDate(event.date, 'monthDay') }}</span>
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ApiError } from '@/api/errors'
import type { Habit, HabitCompleted, Task, TaskCategory } from '@/api/client'
import { todayKey } from '@/composables/calendarDay'
import { formatDate } from '@/composables/formatDate'
import { useNotifications } from '@/composables/useNotifications'
import type { CompletedTask } from '@/stores/tasks'
import { TASK_CATEGORIES } from '@/stores/tasks'
import { daysUntil, useTodayStore } from '@/stores/today'

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

const store = useTodayStore()
const { show: notify } = useNotifications()

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

async function load() {
  const failed = await store.load()
  if (failed.length) notify(`Could not load ${failed.join(', ')}`, 'error')
}

// An installed app resumes where it was left, so a page opened yesterday
// reloads when it comes back on a new day.
function onVisible() {
  if (document.visibilityState === 'visible' && todayKey() !== store.today) void load()
}

onMounted(async () => {
  document.addEventListener('visibilitychange', onVisible)
  // The category row scrolls sideways on a phone, so the remembered choice is brought into view.
  await nextTick()
  categoryRow.value?.querySelector('.today-categories__chip--on')?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' })
  await load()
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisible)
})
</script>
