import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AdminSystemView from '../AdminSystemView.vue'
import AdminSchedulerView from '../AdminSchedulerView.vue'
import AdminUsersView from '../AdminUsersView.vue'
import AdminConfigView from '../AdminConfigView.vue'
import AdminSmokeView from '../AdminSmokeView.vue'
import { useAdminStore } from '@/stores/admin'
import type { SystemHealth, RecentError, SchedulerJob, EnvironmentConfigSection, User } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

const testSystemHealth: SystemHealth = {
  server: {
    environment: 'testing',
    api_url: 'https://api.test.localhost',
    server_time: '2026-03-29T12:00:00Z',
  },
  docker: [
    { name: 'icb-test-api', status: 'running', started_at: '2026-03-29T10:00:00Z', image: 'ichrisbirch:test' },
    { name: 'icb-test-vue', status: 'exited', started_at: null, image: 'ichrisbirch:test' },
  ],
  database: {
    tables: [
      { schema_name: 'public', table_name: 'tasks', row_count: 42 },
      { schema_name: 'public', table_name: 'users', row_count: 3 },
    ],
    total_size_mb: 15.5,
    active_connections: 4,
  },
  redis: {
    key_count: 10,
    memory_used_human: '1.5M',
    connected_clients: 2,
    uptime_seconds: 90061,
  },
  disk: {
    total_gb: 100,
    used_gb: 45,
    free_gb: 55,
    percent_used: 45,
  },
}

const testRecentErrors: RecentError[] = [
  {
    timestamp: '2026-03-29T11:30:00Z',
    method: 'GET',
    path: '/api/tasks/',
    status: 500,
    duration_ms: 120,
    request_id: 'req-abc-123',
  },
]

const testJobs: SchedulerJob[] = [
  {
    id: 'daily-priorities',
    name: 'Update Task Priorities',
    trigger: 'cron[hour=6, minute=0]',
    next_run_time: '2026-03-30T06:00:00Z',
    time_until_next_run: '18h 0m',
    is_paused: false,
  },
  {
    id: 'weekly-prune',
    name: 'Docker Prune',
    trigger: 'cron[day_of_week=sun, hour=3]',
    next_run_time: null,
    time_until_next_run: 'N/A',
    is_paused: true,
  },
]

const testUsers: User[] = [
  {
    id: 1,
    alternative_id: 100,
    name: 'Chris Birch',
    email: 'admin@icb.com',
    is_admin: true,
    created_on: '2024-01-01T00:00:00Z',
    last_login: '2026-03-29T12:00:00Z',
    preferences: { theme_color: 'blue', font_family: 'Inter', dark_mode: true, notifications: true, dashboard_layout: [] },
  },
  {
    id: 2,
    alternative_id: 200,
    name: 'Test User',
    email: 'user@icb.com',
    is_admin: false,
    created_on: '2025-06-15T00:00:00Z',
    last_login: null,
    preferences: { theme_color: 'red', font_family: 'Inter', dark_mode: false, notifications: true, dashboard_layout: [] },
  },
]

const testConfig: EnvironmentConfigSection[] = [
  {
    name: '_general',
    settings: { ENVIRONMENT: 'testing', DEBUG: 'false' },
  },
  {
    name: 'auth',
    settings: { JWT_SECRET: '***MASKED***', TOKEN_EXPIRY: '900' },
  },
]

// --- AdminSystemView ---

function createSystemWrapper(storeState: Record<string, unknown> = {}) {
  return mount(AdminSystemView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            admin: {
              systemHealth: null,
              systemHealthLoading: false,
              recentErrors: [],
              recentErrorsLoading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('AdminSystemView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchSystemHealth and fetchRecentErrors on mount', () => {
    createSystemWrapper()
    const store = useAdminStore()
    expect(store.fetchSystemHealth).toHaveBeenCalledOnce()
    expect(store.fetchRecentErrors).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createSystemWrapper({ systemHealthLoading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders all health sections', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('Server')
    expect(wrapper.text()).toContain('Docker Containers')
    expect(wrapper.text()).toContain('Database')
    expect(wrapper.text()).toContain('Redis')
    expect(wrapper.text()).toContain('Disk')
    expect(wrapper.text()).toContain('Recent Errors')
  })

  it('renders server info', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('testing')
    expect(wrapper.text()).toContain('https://api.test.localhost')
  })

  it('renders docker container rows with status classes', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('icb-test-api')
    expect(wrapper.text()).toContain('icb-test-vue')
    expect(wrapper.find('.admin-status--ok').text()).toBe('running')
    expect(wrapper.find('.admin-status--error').text()).toBe('exited')
  })

  it('renders database stats with size', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('15.5 MB')
    expect(wrapper.text()).toContain('Table Row Counts')
  })

  it('renders redis stats with formatted uptime', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('1.5M')
    expect(wrapper.text()).toContain('1d 1h')
  })

  it('renders disk usage with percentage meter', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('45 / 100 GB')
    expect(wrapper.text()).toContain('45%')
    expect(wrapper.find('.admin-meter__fill--ok').exists()).toBe(true)
  })

  it('applies warn class for high disk usage', () => {
    const highDisk = {
      ...testSystemHealth,
      disk: { ...testSystemHealth.disk, percent_used: 80 },
    }
    const wrapper = createSystemWrapper({ systemHealth: highDisk })
    expect(wrapper.find('.admin-meter__fill--warn').exists()).toBe(true)
  })

  it('applies danger class for critical disk usage', () => {
    const criticalDisk = {
      ...testSystemHealth,
      disk: { ...testSystemHealth.disk, percent_used: 95 },
    }
    const wrapper = createSystemWrapper({ systemHealth: criticalDisk })
    expect(wrapper.find('.admin-meter__fill--danger').exists()).toBe(true)
  })

  it('renders recent errors table', () => {
    const wrapper = createSystemWrapper({
      systemHealth: testSystemHealth,
      recentErrors: testRecentErrors,
    })
    expect(wrapper.text()).toContain('GET')
    expect(wrapper.text()).toContain('/api/tasks/')
    expect(wrapper.text()).toContain('500')
    expect(wrapper.text()).toContain('120ms')
  })

  it('shows empty state when no recent errors', () => {
    const wrapper = createSystemWrapper({ systemHealth: testSystemHealth })
    expect(wrapper.text()).toContain('No recent errors')
  })

  it('shows docker empty state when no containers', () => {
    const noDocker = {
      ...testSystemHealth,
      docker: [],
    }
    const wrapper = createSystemWrapper({ systemHealth: noDocker })
    expect(wrapper.text()).toContain('Docker status unavailable')
  })
})

// --- AdminSchedulerView ---

function createSchedulerWrapper(storeState: Record<string, unknown> = {}) {
  return mount(AdminSchedulerView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            admin: {
              schedulerJobs: [],
              schedulerJobsLoading: false,
              jobHistory: [],
              jobHistoryLoading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('AdminSchedulerView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchSchedulerJobs on mount', () => {
    createSchedulerWrapper()
    const store = useAdminStore()
    expect(store.fetchSchedulerJobs).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createSchedulerWrapper({ schedulerJobsLoading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no jobs', () => {
    const wrapper = createSchedulerWrapper()
    expect(wrapper.text()).toContain('No scheduler jobs found')
  })

  it('renders job cards with details', () => {
    const wrapper = createSchedulerWrapper({ schedulerJobs: testJobs })
    expect(wrapper.text()).toContain('Update Task Priorities')
    expect(wrapper.text()).toContain('cron[hour=6, minute=0]')
    expect(wrapper.text()).toContain('18h 0m')
    expect(wrapper.text()).toContain('Running')
  })

  it('shows Paused badge for paused jobs', () => {
    const wrapper = createSchedulerWrapper({ schedulerJobs: testJobs })
    expect(wrapper.text()).toContain('Docker Prune')
    expect(wrapper.findAll('.admin-status--warn').some((el) => el.text() === 'Paused')).toBe(true)
  })

  it('shows Resume button for paused jobs and Pause for running', () => {
    const wrapper = createSchedulerWrapper({ schedulerJobs: testJobs })
    const buttons = wrapper.findAll('button')
    const buttonTexts = buttons.map((b) => b.text())
    expect(buttonTexts).toContain('Pause')
    expect(buttonTexts).toContain('Resume')
  })

  it('calls pauseJob when Pause clicked', async () => {
    const wrapper = createSchedulerWrapper({ schedulerJobs: testJobs })
    const store = useAdminStore()

    const pauseBtn = wrapper.findAll('button').find((b) => b.text() === 'Pause')!
    await pauseBtn.trigger('click')

    expect(store.pauseJob).toHaveBeenCalledWith('daily-priorities')
  })
})

// --- AdminUsersView ---

function createUsersWrapper(storeState: Record<string, unknown> = {}, authState: Record<string, unknown> = {}) {
  return mount(AdminUsersView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            admin: {
              users: [],
              usersLoading: false,
              error: null,
              ...storeState,
            },
            auth: {
              user: testUsers[0],
              ...authState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('AdminUsersView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchUsers on mount', () => {
    createUsersWrapper()
    const store = useAdminStore()
    expect(store.fetchUsers).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createUsersWrapper({ usersLoading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no users', () => {
    const wrapper = createUsersWrapper()
    expect(wrapper.text()).toContain('No users found')
  })

  it('renders user table with names and emails', () => {
    const wrapper = createUsersWrapper({ users: testUsers })
    expect(wrapper.text()).toContain('Chris Birch')
    expect(wrapper.text()).toContain('admin@icb.com')
    expect(wrapper.text()).toContain('Test User')
    expect(wrapper.text()).toContain('user@icb.com')
  })

  it('shows (you) hint for current user and disables toggle', () => {
    const wrapper = createUsersWrapper({ users: testUsers })
    expect(wrapper.text()).toContain('(you)')
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    // First user (Chris Birch, id: 1) matches auth user — should be disabled
    expect(checkboxes[0]!.attributes('disabled')).toBeDefined()
    // Second user (Test User, id: 2) — should NOT be disabled
    expect(checkboxes[1]!.attributes('disabled')).toBeUndefined()
  })

  it('shows Never for users without last_login', () => {
    const wrapper = createUsersWrapper({ users: testUsers })
    expect(wrapper.text()).toContain('Never')
  })

  it('calls updateUserAdmin when toggling non-self user', async () => {
    const wrapper = createUsersWrapper({ users: testUsers })
    const store = useAdminStore()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[1]!.trigger('change')

    expect(store.updateUserAdmin).toHaveBeenCalledWith(2, true)
  })
})

// --- AdminConfigView ---

function createConfigWrapper(storeState: Record<string, unknown> = {}) {
  return mount(AdminConfigView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            admin: {
              config: [],
              configLoading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('AdminConfigView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchConfig on mount', () => {
    createConfigWrapper()
    const store = useAdminStore()
    expect(store.fetchConfig).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createConfigWrapper({ configLoading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no config', () => {
    const wrapper = createConfigWrapper()
    expect(wrapper.text()).toContain('No configuration loaded')
  })

  it('renders config sections with setting counts', () => {
    const wrapper = createConfigWrapper({ config: testConfig })
    expect(wrapper.text()).toContain('General')
    expect(wrapper.text()).toContain('2 settings')
    expect(wrapper.text()).toContain('Auth')
  })

  it('renders config key-value pairs', () => {
    const wrapper = createConfigWrapper({ config: testConfig })
    expect(wrapper.text()).toContain('ENVIRONMENT')
    expect(wrapper.text()).toContain('testing')
  })

  it('applies masked class to secret values', () => {
    const wrapper = createConfigWrapper({ config: testConfig })
    const maskedEl = wrapper.find('.config-entry__value--masked')
    expect(maskedEl.exists()).toBe(true)
    expect(maskedEl.text()).toBe('***MASKED***')
  })

  it('formats _general section name as General', () => {
    const wrapper = createConfigWrapper({ config: testConfig })
    const summaries = wrapper.findAll('summary')
    expect(summaries[0]!.text()).toContain('General')
  })
})

// --- AdminSmokeView ---

function createSmokeWrapper(storeState: Record<string, unknown> = {}) {
  return mount(AdminSmokeView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            admin: {
              smokeReport: null,
              smokeTestsRunning: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('AdminSmokeView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Run Smoke Tests button', () => {
    const wrapper = createSmokeWrapper()
    expect(wrapper.text()).toContain('Run Smoke Tests')
  })

  it('shows prompt text when no report', () => {
    const wrapper = createSmokeWrapper()
    expect(wrapper.text()).toContain('Click "Run Smoke Tests" to check all endpoints')
  })

  it('disables button and shows Running while tests run', () => {
    const wrapper = createSmokeWrapper({ smokeTestsRunning: true })
    expect(wrapper.text()).toContain('Running...')
    const btn = wrapper.find('button')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('calls runSmokeTests when button clicked', async () => {
    const wrapper = createSmokeWrapper()
    const store = useAdminStore()

    await wrapper.find('button').trigger('click')

    expect(store.runSmokeTests).toHaveBeenCalledOnce()
  })

  it('renders report summary when available', () => {
    const wrapper = createSmokeWrapper({
      smokeReport: {
        run_at: '2026-03-29T12:00:00Z',
        environment: 'testing',
        total: 10,
        passed: 9,
        failed: 1,
        duration_ms: 450,
        all_passed: false,
        results: [
          { path: '/api/tasks/', name: 'tasks list', status_code: 200, response_time_ms: 50, passed: true, error: null },
          {
            path: '/api/broken/',
            name: 'broken endpoint',
            status_code: null,
            response_time_ms: 0,
            passed: false,
            error: 'Connection refused',
          },
        ],
      },
    })
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('testing')
    expect(wrapper.text()).toContain('tasks list')
    expect(wrapper.text()).toContain('Connection refused')
  })
})
