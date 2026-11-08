export interface NavLink {
  // The route, and the key a saved sidebar order names the link by.
  to: string
  label: string
  icon: string
  // Set on a link that leaves this app, which goes here rather than to `to`.
  href?: string
  activeNames?: string[]
}

export const PROJECTS_APP_URL = 'https://projects.ichrisbirch.com/'

export const DEFAULT_SIDEBAR_ORDER = [
  '/',
  '/today',
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
  '/recipes',
  '/shopping',
  '/strains',
  '/tasks',
]

// A saved path with no link is skipped, and a link the order does not name goes last.
export function orderedMainLinks(savedOrder: string[] | undefined): NavLink[] {
  const linkMap = new Map(allMainLinks.map((link) => [link.to, link]))
  const sorted: NavLink[] = []
  for (const path of savedOrder ?? DEFAULT_SIDEBAR_ORDER) {
    const link = linkMap.get(path)
    if (link) {
      sorted.push(link)
      linkMap.delete(path)
    }
  }
  return [...sorted, ...linkMap.values()]
}

export const allMainLinks: NavLink[] = [
  { to: '/', label: 'Home', icon: 'fa-solid fa-house' },
  { to: '/today', label: 'Today', icon: 'fa-solid fa-sun' },
  { to: '/dashboard', label: 'Dashboard', icon: 'fa-solid fa-grip' },
  {
    to: '/articles',
    label: 'Articles',
    icon: 'fa-solid fa-newspaper',
    activeNames: ['articles', 'article-insights', 'article-bulk-import', 'article-stats'],
  },
  { to: '/autofun', label: 'AutoFun', icon: 'fa-solid fa-face-laugh' },
  { to: '/autotasks', label: 'AutoTasks', icon: 'fa-solid fa-robot' },
  { to: '/books', label: 'Books', icon: 'fa-solid fa-book' },
  { to: '/box-packing', label: 'Box Packing', icon: 'fa-solid fa-box' },
  {
    to: '/coffee/shops',
    label: 'Coffee',
    icon: 'fa-solid fa-mug-hot',
    activeNames: ['coffee-shops', 'coffee-beans'],
  },
  { to: '/countdowns', label: 'Countdowns', icon: 'fa-solid fa-hourglass-half' },
  { to: '/durations', label: 'Durations', icon: 'fa-solid fa-clock-rotate-left' },
  { to: '/events', label: 'Events', icon: 'fa-solid fa-calendar' },
  {
    to: '/habits',
    label: 'Habits',
    icon: 'fa-solid fa-repeat',
    activeNames: ['habits', 'habits-completed', 'habits-manage'],
  },
  { to: '/money-wasted', label: 'Money Wasted', icon: 'fa-solid fa-money-bill-wave' },
  { to: '/projects', href: PROJECTS_APP_URL, label: 'Projects', icon: 'fa-solid fa-diagram-project' },
  {
    to: '/recipes',
    label: 'Recipes',
    icon: 'fa-solid fa-utensils',
    activeNames: ['recipes', 'recipe-detail', 'recipes-stats', 'recipes-suggest'],
  },
  { to: '/shopping', label: 'Shopping', icon: 'fa-solid fa-cart-shopping' },
  { to: '/strains', label: 'Strains', icon: 'fa-solid fa-cannabis' },
  {
    to: '/tasks',
    label: 'Tasks',
    icon: 'fa-solid fa-list-check',
    activeNames: ['tasks', 'tasks-todo', 'tasks-completed', 'tasks-search'],
  },
]
