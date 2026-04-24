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
    component: () => import('@/views/VueDashView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/countdowns',
    name: 'countdowns',
    component: () => import('@/views/CountdownsView.vue'),
    meta: { title: 'Countdowns' },
  },
  {
    path: '/durations/stats',
    name: 'durations-stats',
    component: () => import('@/views/DurationsStatsView.vue'),
    meta: { title: 'Durations Stats' },
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
    path: '/books/stats',
    name: 'books-stats',
    component: () => import('@/views/BooksStatsView.vue'),
    meta: { title: 'Books Stats' },
  },
  {
    path: '/books',
    name: 'books',
    component: () => import('@/views/BooksView.vue'),
    meta: { title: 'Books' },
  },
  {
    path: '/coffee',
    redirect: '/coffee/shops',
  },
  {
    path: '/coffee/shops',
    name: 'coffee-shops',
    component: () => import('@/views/CoffeeShopsView.vue'),
    meta: { title: 'Coffee Shops' },
  },
  {
    path: '/coffee/beans',
    name: 'coffee-beans',
    component: () => import('@/views/CoffeeBeansView.vue'),
    meta: { title: 'Coffee Beans' },
  },
  {
    path: '/money-wasted',
    name: 'money-wasted',
    component: () => import('@/views/MoneyWastedView.vue'),
    meta: { title: 'Money Wasted' },
  },
  {
    path: '/autofun/completed',
    name: 'autofun-completed',
    component: () => import('@/views/AutoFunCompletedView.vue'),
    meta: { title: 'AutoFun Completed' },
  },
  {
    path: '/autofun/stats',
    name: 'autofun-stats',
    component: () => import('@/views/AutoFunStatsView.vue'),
    meta: { title: 'AutoFun Stats' },
  },
  {
    path: '/autofun',
    name: 'autofun',
    component: () => import('@/views/AutoFunView.vue'),
    meta: { title: 'AutoFun' },
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
    path: '/articles/stats',
    name: 'article-stats',
    component: () => import('@/views/ArticlesStatsView.vue'),
    meta: { title: 'Articles Stats' },
  },
  {
    path: '/tasks/stats',
    name: 'tasks-stats',
    component: () => import('@/views/TasksStatsView.vue'),
    meta: { title: 'Tasks Stats' },
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('@/views/TasksView.vue'),
    meta: { title: 'Priority Tasks' },
    children: [
      {
        path: 'todo',
        name: 'tasks-todo',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'Outstanding Tasks' },
      },
      {
        path: 'completed',
        name: 'tasks-completed',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'Completed Tasks' },
      },
      {
        path: 'search',
        name: 'tasks-search',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'Tasks Search' },
      },
    ],
  },
  {
    path: '/habits/stats',
    name: 'habits-stats',
    component: () => import('@/views/HabitsStatsView.vue'),
    meta: { title: 'Habits Stats' },
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
    path: '/projects',
    name: 'projects',
    component: () => import('@/views/ProjectsView.vue'),
    meta: { title: 'Projects' },
  },
  {
    path: '/box-packing',
    name: 'box-packing',
    component: () => import('@/views/BoxPackingView.vue'),
    meta: { title: 'Box Packing' },
  },
  {
    path: '/recipes/stats',
    name: 'recipes-stats',
    component: () => import('@/views/RecipesStatsView.vue'),
    meta: { title: 'Recipes Stats' },
  },
  {
    path: '/recipes/suggest',
    name: 'recipes-suggest',
    component: () => import('@/views/RecipesAISuggestView.vue'),
    meta: { title: 'Recipe AI Suggest' },
  },
  {
    path: '/recipes/import-from-url',
    name: 'recipes-import-from-url',
    component: () => import('@/views/RecipesImportFromUrlView.vue'),
    meta: { title: 'Import Recipe from URL' },
  },
  {
    path: '/recipes/cooking-techniques',
    name: 'cooking-techniques',
    component: () => import('@/views/CookingTechniquesView.vue'),
    meta: { title: 'Cooking Techniques' },
  },
  {
    path: '/recipes/cooking-techniques/:slug',
    name: 'cooking-technique-detail',
    component: () => import('@/views/CookingTechniqueDetailView.vue'),
    meta: { title: 'Cooking Technique' },
  },
  {
    path: '/recipes/:id',
    name: 'recipe-detail',
    component: () => import('@/views/RecipeDetailView.vue'),
    meta: { title: 'Recipe' },
  },
  {
    path: '/recipes',
    name: 'recipes',
    component: () => import('@/views/RecipesView.vue'),
    meta: { title: 'Recipes' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: 'Profile' },
  },
  {
    path: '/admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { title: 'Admin', requiresAdmin: true },
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
      {
        path: 'design',
        name: 'admin-design',
        component: () => import('@/views/AdminDesignView.vue'),
        meta: { title: 'Admin — Design' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} | iChrisBirch` : 'iChrisBirch'

  if (to.matched.some((record) => record.meta.requiresAdmin)) {
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    if (!auth.user) {
      await auth.fetchCurrentUser()
    }
    if (!auth.isAdmin) {
      return { name: 'home' }
    }
  }
})

export default router
