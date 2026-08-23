<template>
  <div
    ref="containerRef"
    class="datepicker"
  >
    <div class="datepicker__input-wrapper">
      <input
        :id="id"
        ref="inputRef"
        type="text"
        class="textbox datepicker__input"
        :placeholder="placeholder"
        :required="required"
        :value="displayValue"
        @focus="openCalendar"
        @input="handleTextInput"
        @blur="handleBlur"
        @keydown.escape="closeCalendar"
        @keydown.enter.prevent="commitTextInput"
      />
      <button
        v-if="modelValue && clearable"
        type="button"
        class="datepicker__clear"
        title="Clear date"
        @click.stop="clearDate"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
      <button
        type="button"
        class="datepicker__toggle"
        title="Open calendar"
        @click.stop="toggleCalendar"
      >
        <i class="fa-solid fa-calendar-days"></i>
      </button>
    </div>

    <Teleport to="body">
      <div
        v-if="isOpen"
        class="datepicker__dropdown"
        :style="dropdownStyle"
        @mousedown.prevent
      >
        <div class="datepicker__header">
          <button
            type="button"
            class="datepicker__nav"
            @click="prevMonth"
          >
            <span class="datepicker__nav__text">
              <i class="fa-solid fa-chevron-left"></i>
            </span>
          </button>
          <span class="datepicker__month-year">{{ monthYearLabel }}</span>
          <button
            type="button"
            class="datepicker__nav"
            @click="nextMonth"
          >
            <span class="datepicker__nav__text">
              <i class="fa-solid fa-chevron-right"></i>
            </span>
          </button>
        </div>

        <div class="datepicker__weekdays">
          <span
            v-for="day in weekdays"
            :key="day"
            class="datepicker__weekday"
          >
            {{ day }}
          </span>
        </div>

        <div class="datepicker__days">
          <button
            v-for="(day, index) in calendarDays"
            :key="index"
            type="button"
            class="datepicker__day"
            :class="{
              'datepicker__day--other-month': !day.currentMonth,
              'datepicker__day--selected': day.selected,
              'datepicker__day--today': day.today,
              'datepicker__day--disabled': day.disabled,
            }"
            :disabled="day.disabled"
            @click="selectDay(day)"
          >
            {{ day.date }}
          </button>
        </div>

        <div class="datepicker__footer">
          <button
            v-if="todayInRange"
            type="button"
            class="datepicker__today-btn"
            @click="selectToday"
          >
            Today
          </button>
          <button
            v-if="modelValue && clearable"
            type="button"
            class="datepicker__clear-btn"
            @click="clearDate"
          >
            Clear
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

interface Props {
  modelValue: string // YYYY-MM-DD or empty string
  placeholder?: string
  id?: string
  required?: boolean
  max?: string // YYYY-MM-DD — latest selectable day, inclusive
  clearable?: boolean // false hides both Clear controls, for a caller with no empty state
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'YYYY-MM-DD',
  id: undefined,
  required: false,
  max: undefined,
  clearable: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const isOpen = ref(false)
const viewYear = ref(new Date().getFullYear())
const viewMonth = ref(new Date().getMonth())
const dropdownStyle = ref<Record<string, string>>({})

const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
const monthNames = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

const displayValue = computed(() => {
  if (!props.modelValue) return ''
  const parts = props.modelValue.split('-')
  if (parts.length !== 3) return props.modelValue
  const [y, m, d] = parts
  const date = new Date(Number(y), Number(m) - 1, Number(d))
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const monthYearLabel = computed(() => `${monthNames[viewMonth.value]} ${viewYear.value}`)

interface CalendarDay {
  date: number
  month: number
  year: number
  currentMonth: boolean
  selected: boolean
  today: boolean
  disabled: boolean
}

// Zero-padded YYYY-MM-DD sorts lexicographically, so a string compare is the bound check.
function outOfRange(dateStr: string): boolean {
  return !!props.max && dateStr > props.max
}

const calendarDays = computed((): CalendarDay[] => {
  const days: CalendarDay[] = []
  const today = new Date()
  const todayStr = formatDate(today.getFullYear(), today.getMonth() + 1, today.getDate())

  const firstDay = new Date(viewYear.value, viewMonth.value, 1).getDay()
  const daysInMonth = new Date(viewYear.value, viewMonth.value + 1, 0).getDate()
  const daysInPrevMonth = new Date(viewYear.value, viewMonth.value, 0).getDate()

  // Previous month padding
  for (let i = firstDay - 1; i >= 0; i--) {
    const d = daysInPrevMonth - i
    const m = viewMonth.value === 0 ? 12 : viewMonth.value
    const y = viewMonth.value === 0 ? viewYear.value - 1 : viewYear.value
    const dateStr = formatDate(y, m, d)
    days.push({
      date: d,
      month: m,
      year: y,
      currentMonth: false,
      selected: dateStr === props.modelValue,
      today: dateStr === todayStr,
      disabled: outOfRange(dateStr),
    })
  }

  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = formatDate(viewYear.value, viewMonth.value + 1, d)
    days.push({
      date: d,
      month: viewMonth.value + 1,
      year: viewYear.value,
      currentMonth: true,
      selected: dateStr === props.modelValue,
      today: dateStr === todayStr,
      disabled: outOfRange(dateStr),
    })
  }

  // Next month padding (fill to 42 cells = 6 rows)
  const remaining = 42 - days.length
  for (let d = 1; d <= remaining; d++) {
    const m = viewMonth.value === 11 ? 1 : viewMonth.value + 2
    const y = viewMonth.value === 11 ? viewYear.value + 1 : viewYear.value
    const dateStr = formatDate(y, m, d)
    days.push({
      date: d,
      month: m,
      year: y,
      currentMonth: false,
      selected: dateStr === props.modelValue,
      today: dateStr === todayStr,
      disabled: outOfRange(dateStr),
    })
  }

  return days
})

function formatDate(y: number, m: number, d: number): string {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

// Returns the YYYY-MM-DD form of a typed date, or null when it cannot be parsed or
// falls past max — either way nothing is emitted and the field keeps what it had.
function parseInputDate(input: string): string | null {
  // Try YYYY-MM-DD
  const isoMatch = input.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (isoMatch) {
    const [, y, m, d] = isoMatch
    return acceptedDay(Number(y), Number(m), Number(d))
  }

  // Try MM/DD/YYYY or M/D/YYYY
  const usMatch = input.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/)
  if (usMatch) {
    const [, m, d, y] = usMatch
    return acceptedDay(Number(y), Number(m), Number(d))
  }

  return null
}

// `new Date` rolls an out-of-range component over rather than refusing: day 0 is the
// previous month's last day, and 2026-02-31 is 3 March. Both are non-NaN, so the
// components are compared back to catch a half-typed date before it is emitted.
function acceptedDay(y: number, m: number, d: number): string | null {
  const date = new Date(y, m - 1, d)
  if (isNaN(date.getTime())) return null
  if (date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== d) return null
  const dateStr = formatDate(y, m, d)
  return outOfRange(dateStr) ? null : dateStr
}

function positionDropdown() {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const spaceBelow = window.innerHeight - rect.bottom
  const dropdownHeight = 340

  if (spaceBelow >= dropdownHeight) {
    dropdownStyle.value = {
      top: `${rect.bottom + 4}px`,
      left: `${rect.left}px`,
      minWidth: `${Math.max(rect.width, 280)}px`,
    }
  } else {
    dropdownStyle.value = {
      bottom: `${window.innerHeight - rect.top + 4}px`,
      left: `${rect.left}px`,
      minWidth: `${Math.max(rect.width, 280)}px`,
    }
  }
}

function openCalendar() {
  if (isOpen.value) return
  // Sync view to current value
  if (props.modelValue) {
    // modelValue is always YYYY-MM-DD when non-empty
    viewYear.value = parseInt(props.modelValue.substring(0, 4), 10)
    viewMonth.value = parseInt(props.modelValue.substring(5, 7), 10) - 1
  } else {
    const now = new Date()
    viewYear.value = now.getFullYear()
    viewMonth.value = now.getMonth()
  }
  isOpen.value = true
  nextTick(positionDropdown)
}

function closeCalendar() {
  isOpen.value = false
}

function toggleCalendar() {
  if (isOpen.value) {
    closeCalendar()
  } else {
    openCalendar()
  }
}

function selectDay(day: CalendarDay) {
  if (day.disabled) return
  emit('update:modelValue', formatDate(day.year, day.month, day.date))
  closeCalendar()
}

const todayInRange = computed(() => {
  const now = new Date()
  return !outOfRange(formatDate(now.getFullYear(), now.getMonth() + 1, now.getDate()))
})

function selectToday() {
  const now = new Date()
  emit('update:modelValue', formatDate(now.getFullYear(), now.getMonth() + 1, now.getDate()))
  closeCalendar()
}

function clearDate() {
  emit('update:modelValue', '')
  closeCalendar()
}

function handleTextInput(event: Event) {
  // Allow free typing — we only commit on blur or enter
  const target = event.target as HTMLInputElement
  const parsed = parseInputDate(target.value.trim())
  if (parsed) {
    emit('update:modelValue', parsed)
  }
}

function handleBlur() {
  if (!inputRef.value) return
  const val = inputRef.value.value.trim()
  if (!val) {
    // Emptying the field is a clear, so a caller that has no empty state keeps
    // its value here too — otherwise deleting the text does what the hidden
    // Clear button would have.
    if (props.clearable) emit('update:modelValue', '')
    else inputRef.value.value = displayValue.value
  } else {
    const parsed = parseInputDate(val)
    if (parsed) {
      emit('update:modelValue', parsed)
    } else {
      // Nothing was emitted, so modelValue is unchanged and no re-render will clear
      // the rejected text. Put the accepted value back so the field never lies.
      inputRef.value.value = displayValue.value
    }
  }
  closeCalendar()
}

function commitTextInput() {
  handleBlur()
  inputRef.value?.blur()
}

function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
}

// Close on outside click
function handleClickOutside(event: MouseEvent) {
  if (!containerRef.value) return
  const target = event.target as Node
  // Check if click is inside the container or the teleported dropdown
  if (containerRef.value.contains(target)) return
  const dropdown = document.querySelector('.datepicker__dropdown')
  if (dropdown?.contains(target)) return
  closeCalendar()
}

// Sync view when modelValue changes externally
watch(
  () => props.modelValue,
  (val) => {
    if (val && isOpen.value) {
      viewYear.value = parseInt(val.substring(0, 4), 10)
      viewMonth.value = parseInt(val.substring(5, 7), 10) - 1
    }
  }
)

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
})
</script>
