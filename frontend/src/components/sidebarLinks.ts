export interface NavLink {
  to: string
  label: string
  icon: string
  migrated: boolean
  activeNames?: string[]
}

export const DEFAULT_SIDEBAR_ORDER = [
  '/',
  '/dashboard',
  '/articles',
  '/autofun',
  '/autotasks',
  '/books',
  '/box-packing',
  '/coffee/shops',
  '/countdowns',
  '/durations',
  '/events',
  '/habits',
  '/money-wasted',
  '/projects',
  '/tasks',
]

export const allMainLinks: NavLink[] = [
  { to: '/', label: 'Home', icon: 'fa-solid fa-house', migrated: true },
  { to: '/dashboard', label: 'Dashboard', icon: 'fa-solid fa-grip', migrated: true },
  {
    to: '/articles',
    label: 'Articles',
    icon: 'fa-solid fa-newspaper',
    migrated: true,
    activeNames: ['articles', 'article-insights', 'article-bulk-import', 'article-stats'],
  },
  { to: '/autofun', label: 'AutoFun', icon: 'fa-solid fa-face-laugh', migrated: true },
  { to: '/autotasks', label: 'AutoTasks', icon: 'fa-solid fa-robot', migrated: true },
  { to: '/books', label: 'Books', icon: 'fa-solid fa-book', migrated: true },
  { to: '/box-packing', label: 'Box Packing', icon: 'fa-solid fa-box', migrated: true },
  {
    to: '/coffee/shops',
    label: 'Coffee',
    icon: 'fa-solid fa-mug-hot',
    migrated: true,
    activeNames: ['coffee-shops', 'coffee-beans'],
  },
  { to: '/countdowns', label: 'Countdowns', icon: 'fa-solid fa-hourglass-half', migrated: true },
  { to: '/durations', label: 'Durations', icon: 'fa-solid fa-clock-rotate-left', migrated: true },
  { to: '/events', label: 'Events', icon: 'fa-solid fa-calendar', migrated: true },
  {
    to: '/habits',
    label: 'Habits',
    icon: 'fa-solid fa-repeat',
    migrated: true,
    activeNames: ['habits', 'habits-completed', 'habits-manage'],
  },
  { to: '/money-wasted', label: 'Money Wasted', icon: 'fa-solid fa-money-bill-wave', migrated: true },
  { to: '/projects', label: 'Projects', icon: 'fa-solid fa-diagram-project', migrated: true },
  {
    to: '/tasks',
    label: 'Tasks',
    icon: 'fa-solid fa-list-check',
    migrated: true,
    activeNames: ['tasks', 'tasks-todo', 'tasks-completed', 'tasks-search'],
  },
]
