export interface HomeLink {
  label: string
  url: string
  icon: string
}

export const PROJECT_LINKS: HomeLink[] = [
  { label: 'Code', url: 'https://github.com/datapointchris/ichrisbirch', icon: 'fa-brands fa-github' },
  { label: 'Docs', url: 'https://docs.ichrisbirch.com', icon: 'fa-regular fa-folder-open' },
]

// Each sits behind a login, so the Home page shows them to an admin alone.
export const SERVICE_LINKS: HomeLink[] = [
  { label: 'Chat', url: 'https://chmod.ichrisbirch.com', icon: 'fa-regular fa-message' },
  { label: 'Monitor', url: 'https://monitor.ichrisbirch.com', icon: 'fa-solid fa-chart-line' },
  { label: 'Files', url: 'https://files.ichrisbirch.com', icon: 'fa-solid fa-hard-drive' },
  { label: 'Vault', url: 'https://vault.ichrisbirch.com', icon: 'fa-solid fa-shield-halved' },
  { label: 'Photos', url: 'https://photos.ichrisbirch.com', icon: 'fa-solid fa-images' },
  { label: 'RSS', url: 'https://rss.ichrisbirch.com', icon: 'fa-solid fa-rss' },
  { label: 'Auth', url: 'https://auth.ichrisbirch.com', icon: 'fa-solid fa-lock' },
  { label: 'Learning', url: 'https://learning.ichrisbirch.com', icon: 'fa-solid fa-graduation-cap' },
]
