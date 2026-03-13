import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: 'Home' },
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
    meta: { title: 'Habits' },
  },
  {
    path: '/box-packing',
    name: 'box-packing',
    component: () => import('@/views/BoxPackingView.vue'),
    meta: { title: 'Box Packing' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { title: 'Admin' },
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
