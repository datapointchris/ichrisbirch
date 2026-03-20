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
        @keydown.escape="closeCalendar"
        @keydown.enter.prevent="commitTextInput"
      />
      <button
        v-if="modelValue"
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
            }"
            @click="selectDay(day)"
          >
            {{ day.date }}
          </button>
        </div>

        <div class="datepicker__footer">
          <button
            type="button"
            class="datepicker__today-btn"
            @click="selectToday"
          >
            Today
          </button>
          <button
            v-if="modelValue"
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
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'YYYY-MM-DD',
  id: undefined,
  required: false,
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
    })
  }

  return days
})

function formatDate(y: number, m: number, d: number): string {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function parseInputDate(input: string): string | null {
  // Try YYYY-MM-DD
  const isoMatch = input.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (isoMatch) {
    const [, y, m, d] = isoMatch
    const date = new Date(Number(y), Number(m) - 1, Number(d))
    if (!isNaN(date.getTime())) return formatDate(Number(y), Number(m), Number(d))
  }

  // Try MM/DD/YYYY or M/D/YYYY
  const usMatch = input.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/)
  if (usMatch) {
    const [, m, d, y] = usMatch
    const date = new Date(Number(y), Number(m) - 1, Number(d))
    if (!isNaN(date.getTime())) return formatDate(Number(y), Number(m), Number(d))
  }

  return null
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
  emit('update:modelValue', formatDate(day.year, day.month, day.date))
  closeCalendar()
}

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

function commitTextInput() {
  if (!inputRef.value) return
  const val = inputRef.value.value.trim()
  if (!val) {
    emit('update:modelValue', '')
  } else {
    const parsed = parseInputDate(val)
    if (parsed) {
      emit('update:modelValue', parsed)
    }
  }
  closeCalendar()
  inputRef.value.blur()
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
