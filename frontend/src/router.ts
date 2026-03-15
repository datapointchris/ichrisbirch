import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: 'Home' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/countdowns',
    name: 'countdowns',
    component: () => import('@/views/CountdownsView.vue'),
    meta: { title: 'Countdowns' },
  },
  {
    path: '/durations',
    name: 'durations',
    component: () => import('@/views/DurationsView.vue'),
    meta: { title: 'Durations' },
  },
  {
    path: '/events',
    name: 'events',
    component: () => import('@/views/EventsView.vue'),
    meta: { title: 'Events' },
  },
  {
    path: '/books',
    name: 'books',
    component: () => import('@/views/BooksView.vue'),
    meta: { title: 'Books' },
  },
  {
    path: '/money-wasted',
    name: 'money-wasted',
    component: () => import('@/views/MoneyWastedView.vue'),
    meta: { title: 'Money Wasted' },
  },
  {
    path: '/autotasks',
    name: 'autotasks',
    component: () => import('@/views/AutoTasksView.vue'),
    meta: { title: 'AutoTasks' },
  },
  {
    path: '/articles',
    name: 'articles',
    component: () => import('@/views/ArticlesView.vue'),
    meta: { title: 'Articles' },
  },
  {
    path: '/articles/insights',
    name: 'article-insights',
    component: () => import('@/views/ArticleInsightsView.vue'),
    meta: { title: 'Article Insights' },
  },
  {
    path: '/articles/bulk-import',
    name: 'article-bulk-import',
    component: () => import('@/views/ArticleBulkImportView.vue'),
    meta: { title: 'Bulk Import Articles' },
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('@/views/TasksView.vue'),
    meta: { title: 'Tasks' },
    children: [
      {
        path: 'priority',
        name: 'tasks-priority',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'Tasks — Priority' },
      },
      {
        path: 'completed',
        name: 'tasks-completed',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'Tasks — Completed' },
      },
    ],
  },
  {
    path: '/habits',
    name: 'habits',
    component: () => import('@/views/HabitsView.vue'),
    meta: { title: 'Daily Habits' },
  },
  {
    path: '/habits/completed',
    name: 'habits-completed',
    component: () => import('@/views/HabitsCompletedView.vue'),
    meta: { title: 'Completed Habits' },
  },
  {
    path: '/habits/manage',
    name: 'habits-manage',
    component: () => import('@/views/HabitsManageView.vue'),
    meta: { title: 'Manage Habits' },
  },
  {
    path: '/box-packing',
    name: 'box-packing',
    component: () => import('@/views/BoxPackingAllView.vue'),
    meta: { title: 'All Boxes' },
  },
  {
    path: '/box-packing/box/:id',
    name: 'box-packing-detail',
    component: () => import('@/views/BoxPackingDetailView.vue'),
    meta: { title: 'Box Detail' },
  },
  {
    path: '/box-packing/orphans',
    name: 'box-packing-orphans',
    component: () => import('@/views/BoxPackingOrphansView.vue'),
    meta: { title: 'Orphaned Items' },
  },
  {
    path: '/box-packing/search',
    name: 'box-packing-search',
    component: () => import('@/views/BoxPackingSearchView.vue'),
    meta: { title: 'Search Items' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: 'Profile' },
  },
  {
    path: '/profile/settings',
    name: 'profile-settings',
    component: () => import('@/views/ProfileSettingsView.vue'),
    meta: { title: 'Settings' },
  },
  {
    path: '/admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { title: 'Admin' },
    children: [
      {
        path: '',
        name: 'admin',
        component: () => import('@/views/AdminSystemView.vue'),
        meta: { title: 'Admin — System' },
      },
      {
        path: 'scheduler',
        name: 'admin-scheduler',
        component: () => import('@/views/AdminSchedulerView.vue'),
        meta: { title: 'Admin — Scheduler' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/AdminUsersView.vue'),
        meta: { title: 'Admin — Users' },
      },
      {
        path: 'config',
        name: 'admin-config',
        component: () => import('@/views/AdminConfigView.vue'),
        meta: { title: 'Admin — Config' },
      },
      {
        path: 'smoke',
        name: 'admin-smoke',
        component: () => import('@/views/AdminSmokeView.vue'),
        meta: { title: 'Admin — Smoke Tests' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} | iChrisBirch` : 'iChrisBirch'
})

export default router
