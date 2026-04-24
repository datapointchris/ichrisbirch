import type { SubnavLink } from '@/components/AppSubnav.vue'

export const HABITS_SUBNAV: SubnavLink[] = [
  { label: 'Daily Habits', to: '/habits', testId: 'habits-subnav-daily', icon: 'fa-solid fa-check-double' },
  { label: 'Completed', to: '/habits/completed', testId: 'habits-subnav-completed', icon: 'fa-solid fa-circle-check' },
  { label: 'Manage', to: '/habits/manage', testId: 'habits-subnav-manage', icon: 'fa-solid fa-list-check' },
  { label: 'Stats', to: '/habits/stats', testId: 'habits-subnav-stats', icon: 'fa-solid fa-chart-bar' },
]

export const ARTICLES_SUBNAV: SubnavLink[] = [
  { label: 'All Articles', to: '/articles', testId: 'articles-subnav-all', icon: 'fa-solid fa-newspaper' },
  { label: 'Bulk Import', to: '/articles/bulk-import', testId: 'articles-subnav-bulk-import', icon: 'fa-solid fa-file-import' },
  { label: 'Insights', to: '/articles/insights', testId: 'articles-subnav-insights', icon: 'fa-solid fa-lightbulb' },
  { label: 'Stats', to: '/articles/stats', testId: 'articles-subnav-stats', icon: 'fa-solid fa-chart-bar' },
]

export const TASKS_SUBNAV: SubnavLink[] = [
  { label: 'Priority Tasks', to: '/tasks', icon: 'fa-solid fa-fire' },
  { label: 'Outstanding Tasks', to: '/tasks/todo', icon: 'fa-solid fa-list' },
  { label: 'Completed Tasks', to: '/tasks/completed', icon: 'fa-solid fa-circle-check' },
  { label: 'Stats', to: '/tasks/stats', icon: 'fa-solid fa-chart-bar' },
]

export const BOOKS_SUBNAV: SubnavLink[] = [
  { label: 'Books', to: '/books', icon: 'fa-solid fa-book' },
  { label: 'Stats', to: '/books/stats', icon: 'fa-solid fa-chart-bar' },
]

export const RECIPES_SUBNAV: SubnavLink[] = [
  { label: 'Recipes', to: '/recipes', testId: 'recipes-subnav-list', icon: 'fa-solid fa-utensils' },
  {
    label: 'Techniques',
    to: '/recipes/cooking-techniques',
    testId: 'recipes-subnav-techniques',
    icon: 'fa-solid fa-mortar-pestle',
  },
  { label: 'AI Suggest', to: '/recipes/suggest', testId: 'recipes-subnav-suggest', icon: 'fa-solid fa-wand-magic-sparkles' },
  { label: 'Stats', to: '/recipes/stats', testId: 'recipes-subnav-stats', icon: 'fa-solid fa-chart-bar' },
]

export const DURATIONS_SUBNAV: SubnavLink[] = [
  { label: 'Durations', to: '/durations', icon: 'fa-solid fa-hourglass-half' },
  { label: 'Stats', to: '/durations/stats', icon: 'fa-solid fa-chart-bar' },
]

export const AUTOFUN_SUBNAV: SubnavLink[] = [
  { label: 'Fun List', to: '/autofun', icon: 'fa-solid fa-dice' },
  { label: 'Completed', to: '/autofun/completed', icon: 'fa-solid fa-circle-check' },
  { label: 'Stats', to: '/autofun/stats', icon: 'fa-solid fa-chart-bar' },
]

export const COFFEE_SUBNAV: SubnavLink[] = [
  { label: 'Shops', to: '/coffee/shops', testId: 'coffee-subnav-shops', icon: 'fa-solid fa-mug-hot' },
  { label: 'Beans', to: '/coffee/beans', testId: 'coffee-subnav-beans', icon: 'fa-solid fa-seedling' },
]

export const ADMIN_SUBNAV: SubnavLink[] = [
  { label: 'System Health', to: '/admin', testId: 'admin-subnav-system', icon: 'fa-solid fa-heart-pulse' },
  { label: 'Scheduler', to: '/admin/scheduler', testId: 'admin-subnav-scheduler', icon: 'fa-solid fa-clock' },
  { label: 'Users', to: '/admin/users', testId: 'admin-subnav-users', icon: 'fa-solid fa-users' },
  { label: 'Config', to: '/admin/config', testId: 'admin-subnav-config', icon: 'fa-solid fa-sliders' },
  { label: 'Smoke Tests', to: '/admin/smoke', testId: 'admin-subnav-smoke', icon: 'fa-solid fa-vial' },
  { label: 'Design', to: '/admin/design', testId: 'admin-subnav-design', icon: 'fa-solid fa-palette' },
  { label: 'AutoTasks', to: '/autotasks', testId: 'admin-subnav-autotasks', icon: 'fa-solid fa-robot' },
]
