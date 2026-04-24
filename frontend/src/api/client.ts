import axios from 'axios'
import { createLogger } from '@/utils/logger'
import { extractApiError } from './errors'

const logger = createLogger('ApiClient')

const apiUrl = import.meta.env.VITE_API_URL || 'https://api.docker.localhost'

// Track request metadata (start time, request ID) outside Axios's config object.
// WeakMap avoids type augmentation issues and cleans up automatically.
interface RequestMeta {
  startTime: number
  requestId: string
}
const requestMeta = new WeakMap<object, RequestMeta>()

export const api = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: true,
})

// Request interceptor: inject X-Request-ID and log outgoing request
api.interceptors.request.use((config) => {
  const requestId = crypto.randomUUID().slice(0, 8)
  config.headers.set('X-Request-ID', requestId)

  requestMeta.set(config, { startTime: Date.now(), requestId })

  logger.debug('request_outgoing', {
    method: config.method?.toUpperCase(),
    url: `${config.baseURL}${config.url}`,
    request_id: requestId,
  })

  return config
})

// Response interceptor: log response and convert errors to ApiError
api.interceptors.response.use(
  (response) => {
    const meta = requestMeta.get(response.config)
    const duration = meta ? Date.now() - meta.startTime : 0

    logger.info('request_completed', {
      method: response.config.method?.toUpperCase(),
      url: `${response.config.baseURL}${response.config.url}`,
      status: response.status,
      duration_ms: duration,
      request_id: meta?.requestId,
    })

    return response
  },
  (error) => {
    const meta = error.config ? requestMeta.get(error.config) : undefined
    const duration = meta ? Date.now() - meta.startTime : 0
    const apiError = extractApiError(error)

    if (apiError.isNetworkError) {
      logger.error('request_network_error', {
        method: error.config?.method?.toUpperCase(),
        url: error.config ? `${error.config.baseURL}${error.config.url}` : 'unknown',
        error: apiError.detail,
        duration_ms: duration,
        request_id: meta?.requestId,
      })
    } else {
      logger.error('request_failed', {
        method: error.config?.method?.toUpperCase(),
        url: error.config ? `${error.config.baseURL}${error.config.url}` : 'unknown',
        status: apiError.status,
        detail: apiError.detail,
        duration_ms: duration,
        request_id: apiError.requestId || meta?.requestId,
      })
    }

    return Promise.reject(apiError)
  }
)

// Re-export all types so existing imports from '@/api/client' continue to work
export type {
  TaskCategory,
  AutoFun,
  AutoFunCreate,
  AutoFunUpdate,
  AutoFunPreferences,
  AutoTaskFrequency,
  BoxSize,
  UserPreferences,
  User,
  PersonalApiKey,
  PersonalApiKeyCreate,
  PersonalApiKeyCreated,
  Countdown,
  CountdownCreate,
  CountdownUpdate,
  DurationNote,
  DurationNoteCreate,
  DurationNoteUpdate,
  Duration,
  DurationCreate,
  DurationUpdate,
  Event,
  EventCreate,
  EventUpdate,
  Task,
  TaskCreate,
  TaskUpdate,
  Book,
  BookCreate,
  BookUpdate,
  BookGoodreadsInfo,
  Article,
  ArticleCreate,
  ArticleUpdate,
  ArticleSummary,
  BulkImportResponse,
  BulkImportStatus,
  HabitCategory,
  Habit,
  HabitCreate,
  HabitUpdate,
  HabitCompleted,
  HabitCategoryCreate,
  HabitCategoryUpdate,
  HabitCompletedCreate,
  AutoTask,
  AutoTaskCreate,
  AutoTaskUpdate,
  MoneyWasted,
  MoneyWastedCreate,
  MoneyWastedUpdate,
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectWithItemCount,
  ProjectItem,
  ProjectItemCreate,
  ProjectItemUpdate,
  ProjectItemDetail,
  ProjectItemInProject,
  ProjectItemReorder,
  ProjectItemMembershipCreate,
  ProjectItemDependencyCreate,
  ProjectItemTask,
  ProjectItemTaskCreate,
  ProjectItemTaskUpdate,
  BoxItem,
  BoxItemCreate,
  BoxItemUpdate,
  Box,
  BoxCreate,
  BoxUpdate,
  BoxSearchResult,
  SchedulerJob,
  SchedulerJobRun,
  DockerContainerStatus,
  TableRowCount,
  DatabaseStats,
  RedisStats,
  DiskUsage,
  ServerInfo,
  SystemHealth,
  RecentError,
  EnvironmentConfigSection,
  SmokeTestResult,
  SmokeTestReport,
  RoastLevel,
  BrewMethod,
  CoffeeShop,
  CoffeeShopCreate,
  CoffeeShopUpdate,
  CoffeeBean,
  CoffeeBeanCreate,
  CoffeeBeanUpdate,
  RecipeDifficulty,
  RecipeCuisine,
  RecipeMealType,
  RecipeUnit,
  RecipeIngredient,
  RecipeIngredientCreate,
  Recipe,
  RecipeCreate,
  RecipeUpdate,
  RecipeIngredientSearchResult,
  RecipeSuggestionRequest,
  RecipeCandidate,
  RecipeSuggestionResponse,
  RecipeRatingBreakdown,
  RecipeCategoryBreakdown,
  RecipeStats,
  CookingTechniqueCategory,
  CookingTechnique,
  CookingTechniqueCreate,
  CookingTechniqueUpdate,
  CookingTechniqueCategoryBreakdown,
  UrlImportKind,
  UrlImportHint,
  UrlImportRequest,
  UrlImportCandidate,
  UrlImportResponse,
  UrlImportSaveResult,
} from './types'
