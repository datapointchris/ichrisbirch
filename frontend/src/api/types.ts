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
  | 'Research'
  | 'Work'

export type AutoTaskFrequency = 'Daily' | 'Weekly' | 'Biweekly' | 'Monthly' | 'Quarterly' | 'Semiannually' | 'Yearly'

export type BoxSize = 'Book' | 'Small' | 'Medium' | 'Large' | 'Bag' | 'Monitor' | 'Misc' | 'Sixteen' | 'UhaulSmall'

// --- User ---

export interface UserPreferences {
  theme_color: string
  font_family: string
  dark_mode: boolean
  notifications: boolean
  dashboard_layout: string[][]
  [key: string]: unknown
}

export interface User {
  id: number
  alternative_id: number
  name: string
  email: string
  is_admin: boolean
  created_on: string
  last_login?: string
  preferences: UserPreferences
}

// --- Personal API Key ---

export interface PersonalApiKey {
  id: number
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
  revoked_at: string | null
}

export interface PersonalApiKeyCreate {
  name: string
}

export interface PersonalApiKeyCreated extends PersonalApiKey {
  key: string
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

// --- Duration ---

export interface DurationNote {
  id: number
  duration_id: number
  date: string
  content: string
}

export interface DurationNoteCreate {
  date: string
  content: string
}

export interface DurationNoteUpdate {
  date?: string
  content?: string
}

export interface Duration {
  id: number
  name: string
  start_date: string
  end_date?: string
  notes?: string
  color?: string
  duration_notes: DurationNote[]
}

export interface DurationCreate {
  name: string
  start_date: string
  end_date?: string
  notes?: string
  color?: string
}

export interface DurationUpdate {
  name?: string
  start_date?: string
  end_date?: string | null
  notes?: string
  color?: string
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
  location?: string
  notes?: string
  ownership: string
  progress: string
  reject_reason?: string
  review?: string
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
  review?: string
}

export interface BookUpdate {
  isbn?: string | null
  title?: string
  author?: string
  tags?: string[]
  goodreads_url?: string | null
  priority?: number | null
  purchase_date?: string | null
  purchase_price?: number | null
  sell_date?: string | null
  sell_price?: number | null
  read_start_date?: string | null
  read_finish_date?: string | null
  rating?: number | null
  abandoned?: boolean
  location?: string | null
  notes?: string | null
  review?: string | null
}

export interface BookGoodreadsInfo {
  title: string
  author: string
  tags: string
  goodreads_url: string
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

export interface ArticleSummary {
  title: string
  summary: string
  tags: string[]
}

export interface BulkImportResponse {
  batch_id: string
  total: number
  status: string
}

export interface BulkImportStatus {
  batch_id: string
  status: 'queued' | 'processing' | 'completed'
  total: number
  processed: number
  succeeded: number
  failed_count: number
  errors: { url: string; error: string }[]
  results: { url: string }[]
  created_at: string
  updated_at: string
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

export interface HabitCategoryCreate {
  name: string
  is_current?: boolean
}

export interface HabitCategoryUpdate {
  name?: string
  is_current?: boolean
}

export interface HabitCompletedCreate {
  name: string
  category_id: number
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

// --- Project ---

export interface Project {
  id: number
  name: string
  position: number
  created_at: string
}

export interface ProjectCreate {
  name: string
  position?: number
}

export interface ProjectUpdate {
  name?: string
  position?: number
}

export interface ProjectWithItemCount extends Project {
  item_count: number
}

export interface ProjectItem {
  id: number
  title: string
  notes?: string
  completed: boolean
  archived: boolean
  created_at: string
  updated_at: string
}

export interface ProjectItemCreate {
  title: string
  notes?: string
  project_ids: number[]
}

export interface ProjectItemUpdate {
  title?: string
  notes?: string
  completed?: boolean
  archived?: boolean
}

export interface ProjectItemDetail extends ProjectItem {
  projects: Project[]
  dependency_ids: number[]
}

export interface ProjectItemInProject extends ProjectItem {
  position: number
}

export interface ProjectItemReorder {
  project_id: number
  position: number
}

export interface ProjectItemMembershipCreate {
  project_id: number
}

export interface ProjectItemDependencyCreate {
  depends_on_id: number
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
  box_id?: number | null
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

export interface BoxSearchResult {
  box: Box
  item: BoxItem
}

// --- Admin ---

export interface SchedulerJob {
  id: string
  name: string
  trigger: string
  next_run_time: string | null
  time_until_next_run: string
  is_paused: boolean
}

export interface SchedulerJobRun {
  id: number
  job_id: string
  started_at: string
  finished_at: string
  duration_seconds: number
  success: boolean
  error_type: string | null
  error_message: string | null
}

export interface DockerContainerStatus {
  name: string
  status: string
  started_at: string | null
  image: string
}

export interface TableRowCount {
  schema_name: string
  table_name: string
  row_count: number
}

export interface DatabaseStats {
  tables: TableRowCount[]
  total_size_mb: number
  active_connections: number
}

export interface RedisStats {
  key_count: number
  memory_used_human: string
  connected_clients: number
  uptime_seconds: number
}

export interface DiskUsage {
  total_gb: number
  used_gb: number
  free_gb: number
  percent_used: number
}

export interface ServerInfo {
  environment: string
  api_url: string
  server_time: string
}

export interface SystemHealth {
  server: ServerInfo
  docker: DockerContainerStatus[]
  database: DatabaseStats
  redis: RedisStats
  disk: DiskUsage
}

export interface RecentError {
  timestamp: string
  method: string
  path: string
  status: number
  duration_ms: number
  request_id: string
}

export interface EnvironmentConfigSection {
  name: string
  settings: Record<string, unknown>
}

export interface SmokeTestResult {
  path: string
  name: string
  status_code: number | null
  response_time_ms: number
  passed: boolean
  error: string | null
}

export interface SmokeTestReport {
  run_at: string
  environment: string
  total: number
  passed: number
  failed: number
  duration_ms: number
  all_passed: boolean
  results: SmokeTestResult[]
}
