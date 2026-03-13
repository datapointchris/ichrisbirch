import axios from 'axios'

const apiUrl = import.meta.env.VITE_API_URL || 'https://api.docker.localhost'

export const api = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const lastReload = sessionStorage.getItem('lastAuthReload')
      const now = Date.now()
      if (!lastReload || now - Number(lastReload) > 60000) {
        sessionStorage.setItem('lastAuthReload', String(now))
        window.location.reload()
        return new Promise(() => {})
      }
    }

    const message = error.response?.data?.detail || error.message || 'An error occurred'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

// --- Enums ---

export type TaskCategory =
  | 'Automotive'
  | 'Chore'
  | 'Computer'
  | 'Dingo'
  | 'Financial'
  | 'Home'
  | 'Kitchen'
  | 'Learn'
  | 'Personal'
  | 'Purchase'

export type AutoTaskFrequency = 'Daily' | 'Weekly' | 'Biweekly' | 'Monthly' | 'Quarterly' | 'Semiannually' | 'Yearly'

export type BoxSize = 'Book' | 'Small' | 'Medium' | 'Large' | 'Bag' | 'Monitor' | 'Misc' | 'Sixteen' | 'UhaulSmall'

// --- User ---

export interface User {
  id: number
  alternative_id: number
  name: string
  email: string
  is_admin: boolean
  created_on: string
  last_login?: string
}

// --- Countdown ---

export interface Countdown {
  id: number
  name: string
  notes?: string
  due_date: string
}

export interface CountdownCreate {
  name: string
  notes?: string
  due_date: string
}

export interface CountdownUpdate {
  name?: string
  notes?: string
  due_date?: string
}

// --- Event ---

export interface Event {
  id: number
  name: string
  date: string
  venue: string
  url?: string
  cost: number
  attending: boolean
  notes?: string
}

export interface EventCreate {
  name: string
  date: string
  venue: string
  url?: string
  cost: number
  attending: boolean
  notes?: string
}

export interface EventUpdate {
  name?: string
  date?: string
  venue?: string
  url?: string
  cost?: number
  attending?: boolean
  notes?: string
}

// --- Task ---

export interface Task {
  id: number
  name: string
  notes?: string
  category: TaskCategory
  priority: number
  add_date: string
  complete_date?: string
}

export interface TaskCreate {
  name: string
  notes?: string
  category: TaskCategory
  priority: number
}

export interface TaskUpdate {
  name?: string
  notes?: string
  category?: TaskCategory
  priority?: number
  add_date?: string
  complete_date?: string
}

// --- Book ---

export interface Book {
  id: number
  isbn?: string
  title: string
  author: string
  tags: string[]
  goodreads_url?: string
  priority?: number
  purchase_date?: string
  purchase_price?: number
  sell_date?: string
  sell_price?: number
  read_start_date?: string
  read_finish_date?: string
  rating?: number
  abandoned?: boolean
  location?: string
  notes?: string
}

export interface BookCreate {
  isbn?: string
  title: string
  author: string
  tags: string[]
  goodreads_url?: string
  priority?: number
  purchase_date?: string
  purchase_price?: number
  sell_date?: string
  sell_price?: number
  read_start_date?: string
  read_finish_date?: string
  rating?: number
  abandoned?: boolean
  location?: string
  notes?: string
}

export interface BookUpdate {
  isbn?: string
  title?: string
  author?: string
  tags?: string[]
  goodreads_url?: string
  priority?: number
  purchase_date?: string
  purchase_price?: number
  sell_date?: string
  sell_price?: number
  read_start_date?: string
  read_finish_date?: string
  rating?: number
  abandoned?: boolean
  location?: string
  notes?: string
}

// --- Article ---

export interface Article {
  id: number
  title: string
  url: string
  tags: string[]
  summary: string
  notes?: string
  save_date: string
  last_read_date?: string
  read_count: number
  is_favorite: boolean
  is_current: boolean
  is_archived: boolean
  review_days?: number
}

export interface ArticleCreate {
  title: string
  url: string
  tags?: string[]
  summary: string
  notes?: string
  save_date: string
  read_count?: number
  is_favorite?: boolean
  is_current?: boolean
  is_archived?: boolean
  review_days?: number
}

export interface ArticleUpdate {
  title?: string
  tags?: string[]
  summary?: string
  notes?: string
  is_favorite?: boolean
  is_current?: boolean
  is_archived?: boolean
  last_read_date?: string
  read_count?: number
  review_days?: number
}

// --- Habit ---

export interface HabitCategory {
  id: number
  name: string
  is_current: boolean
}

export interface Habit {
  id: number
  name: string
  category_id: number
  category: HabitCategory
  is_current: boolean
}

export interface HabitCreate {
  name: string
  category_id: number
  is_current?: boolean
}

export interface HabitUpdate {
  name?: string
  category_id?: number
  is_current?: boolean
}

export interface HabitCompleted {
  id: number
  name: string
  category_id: number
  category: HabitCategory
  complete_date: string
}

// --- AutoTask ---

export interface AutoTask {
  id: number
  name: string
  category: TaskCategory
  priority: number
  notes?: string
  frequency: AutoTaskFrequency
  max_concurrent: number
  first_run_date: string
  last_run_date: string
  run_count: number
}

export interface AutoTaskCreate {
  name: string
  notes?: string
  category: TaskCategory
  priority: number
  frequency: AutoTaskFrequency
  max_concurrent?: number
}

export interface AutoTaskUpdate {
  name?: string
  category?: TaskCategory
  priority?: number
  notes?: string
  frequency?: AutoTaskFrequency
  max_concurrent?: number
}

// --- Money Wasted ---

export interface MoneyWasted {
  id: number
  item: string
  amount: number
  date_purchased?: string
  date_wasted: string
  notes?: string
}

export interface MoneyWastedCreate {
  item: string
  amount: number
  date_purchased?: string
  date_wasted: string
  notes?: string
}

export interface MoneyWastedUpdate {
  item?: string
  amount?: number
  date_purchased?: string
  date_wasted?: string
  notes?: string
}

// --- Box Packing ---

export interface BoxItem {
  id: number
  box_id?: number
  name: string
  essential: boolean
  warm: boolean
  liquid: boolean
}

export interface BoxItemCreate {
  box_id: number
  name: string
  essential: boolean
  warm: boolean
  liquid: boolean
}

export interface BoxItemUpdate {
  box_id?: number
  name?: string
  essential?: boolean
  warm?: boolean
  liquid?: boolean
}

export interface Box {
  id: number
  number?: number
  name: string
  size: BoxSize
  essential: boolean
  warm: boolean
  liquid: boolean
  items: BoxItem[]
}

export interface BoxCreate {
  name: string
  number?: number
  size: BoxSize
  essential: boolean
  warm: boolean
  liquid: boolean
}

export interface BoxUpdate {
  name?: string
  number?: number
  size?: BoxSize
  essential?: boolean
  warm?: boolean
  liquid?: boolean
}
