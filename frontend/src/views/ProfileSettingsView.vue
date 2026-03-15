<template>
  <ProfileSubnav active="settings" />

  <div class="grid grid--one-column">
    <div
      v-if="auth.loading"
      class="grid__item"
    >
      Loading...
    </div>
    <div
      v-else-if="!auth.user"
      class="grid__item"
    >
      Unable to load user data.
    </div>
    <template v-else>
      <div class="grid__item">
        <h1>{{ auth.user.name }}</h1>
        <h2>Settings</h2>
      </div>

      <!-- Appearance -->
      <div class="grid__item">
        <h3>Appearance</h3>

        <div class="setting-row">
          <label class="setting-row__label">Theme Color</label>
          <div class="theme-colors">
            <button
              v-for="color in themeColors"
              :key="color"
              class="theme-colors__swatch"
              :class="{ 'theme-colors__swatch--selected': selectedThemeColor === color }"
              :style="{ background: colorMap[color] }"
              :title="color"
              @click="selectThemeColor(color)"
            >
              <span class="theme-colors__label">{{ color }}</span>
            </button>
          </div>
        </div>

        <div class="setting-row">
          <label
            class="setting-row__label"
            for="dark-mode"
            >Dark Mode</label
          >
          <input
            id="dark-mode"
            v-model="darkMode"
            type="checkbox"
            @change="saveDarkMode"
          />
        </div>
      </div>

      <!-- API Keys -->
      <div class="grid__item">
        <h3>Personal API Keys</h3>
        <p class="setting-description">API keys allow external tools to access your data without a browser session.</p>

        <div
          v-if="newlyCreatedKey"
          class="api-key-banner"
        >
          <strong>Copy this key now — it will not be shown again:</strong>
          <code class="api-key-banner__key">{{ newlyCreatedKey }}</code>
          <button
            class="button button--small"
            @click="copyKey"
          >
            Copy
          </button>
        </div>

        <table
          v-if="auth.apiKeys.length > 0"
          class="api-keys-table"
        >
          <thead>
            <tr>
              <th>Name</th>
              <th>Key Prefix</th>
              <th>Created</th>
              <th>Last Used</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="key in auth.apiKeys"
              :key="key.id"
            >
              <td>{{ key.name }}</td>
              <td>
                <code>{{ key.key_prefix }}...</code>
              </td>
              <td>{{ formatDate(key.created_at) }}</td>
              <td>{{ key.last_used_at ? formatDate(key.last_used_at) : 'Never' }}</td>
              <td>
                <span :class="key.revoked_at ? 'status--revoked' : 'status--active'">
                  {{ key.revoked_at ? 'Revoked' : 'Active' }}
                </span>
              </td>
              <td>
                <button
                  v-if="!key.revoked_at"
                  class="button button--small button--danger"
                  @click="handleRevokeKey(key.id)"
                >
                  Revoke
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p
          v-else
          class="setting-description"
        >
          No API keys created yet.
        </p>

        <form
          class="api-key-form"
          @submit.prevent="handleCreateKey"
        >
          <label for="key-name">Key Name</label>
          <div class="api-key-form__row">
            <input
              id="key-name"
              v-model="keyName"
              type="text"
              placeholder="e.g., Claude Code MCP"
              required
            />
            <button
              type="submit"
              class="button"
            >
              Create API Key
            </button>
          </div>
        </form>
      </div>

      <!-- Actions -->
      <div class="grid__item">
        <h3>Actions</h3>
        <button
          class="button"
          @click="handleResetPriorities"
        >
          Reset Task Priorities
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import ProfileSubnav from '@/components/ProfileSubnav.vue'

const auth = useAuthStore()
const { show: notify } = useNotifications()

const themeColors = ['turquoise', 'blue', 'green', 'orange', 'red', 'purple', 'yellow', 'pink', 'random'] as const

const colorMap: Record<string, string> = {
  turquoise: '#1abc9c',
  blue: '#2980b9',
  green: '#27ae60',
  orange: '#e67e22',
  red: '#e74c3c',
  purple: '#8e44ad',
  yellow: '#f1c40f',
  pink: '#e91e63',
  random: 'linear-gradient(135deg, #e74c3c, #f1c40f, #27ae60, #2980b9, #8e44ad)',
}

const selectedThemeColor = ref(auth.preferences?.theme_color ?? 'turquoise')
const darkMode = ref(auth.preferences?.dark_mode ?? true)
const keyName = ref('')
const newlyCreatedKey = ref<string | null>(null)

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

function formatDate(dateStr: string): string {
  return dateFormatter.format(new Date(dateStr))
}

async function selectThemeColor(color: string) {
  selectedThemeColor.value = color
  try {
    await auth.updatePreferences({ theme_color: color })
    notify(`Theme color set to ${color}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update theme: ${detail}`, 'error')
  }
}

async function saveDarkMode() {
  try {
    await auth.updatePreferences({ dark_mode: darkMode.value })
    notify(`Dark mode ${darkMode.value ? 'enabled' : 'disabled'}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update dark mode: ${detail}`, 'error')
  }
}

async function handleCreateKey() {
  const name = keyName.value.trim()
  if (!name) return
  try {
    const created = await auth.createApiKey(name)
    newlyCreatedKey.value = created.key
    keyName.value = ''
    notify('API key created', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to create API key: ${detail}`, 'error')
  }
}

async function copyKey() {
  if (newlyCreatedKey.value) {
    await navigator.clipboard.writeText(newlyCreatedKey.value)
    notify('Key copied to clipboard', 'success')
  }
}

async function handleRevokeKey(id: number) {
  if (!confirm('Revoke this API key? This cannot be undone.')) return
  try {
    await auth.revokeApiKey(id)
    notify('API key revoked', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to revoke API key: ${detail}`, 'error')
  }
}

async function handleResetPriorities() {
  try {
    const result = await auth.resetTaskPriorities()
    notify(result.message, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to reset priorities: ${detail}`, 'error')
  }
}

onMounted(async () => {
  if (!auth.user) {
    await auth.fetchCurrentUser()
  }
  await auth.fetchApiKeys()
  // Sync local state with loaded preferences
  if (auth.preferences) {
    selectedThemeColor.value = auth.preferences.theme_color
    darkMode.value = auth.preferences.dark_mode
  }
})
</script>

<style scoped>
.setting-row {
  display: flex;
  align-items: center;
  gap: var(--space-m);
  margin-bottom: var(--space-s);
}

.setting-row__label {
  min-width: 8rem;
  color: var(--clr-gray-400);
  font-weight: 600;
}

.setting-description {
  color: var(--clr-gray-400);
  margin-bottom: var(--space-s);
}

/* Theme color swatches */
.theme-colors {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.theme-colors__swatch {
  width: 3rem;
  height: 3rem;
  border-radius: 0.5rem;
  border: 3px solid transparent;
  cursor: pointer;
  transition:
    border-color 0.2s,
    transform 0.15s;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  overflow: hidden;
}

.theme-colors__swatch:hover {
  transform: scale(1.1);
}

.theme-colors__swatch--selected {
  border-color: var(--clr-gray-100);
}

.theme-colors__label {
  font-size: 0.55rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
  padding-bottom: 0.15rem;
  text-transform: capitalize;
}

/* API key banner */
.api-key-banner {
  background: var(--clr-gray-800);
  border: 2px solid var(--clr-primary-400);
  border-radius: 0.5rem;
  padding: var(--space-s);
  margin-bottom: var(--space-m);
  display: flex;
  align-items: center;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.api-key-banner__key {
  font-family: monospace;
  background: var(--clr-gray-900);
  padding: var(--space-3xs) var(--space-xs);
  border-radius: 0.25rem;
  word-break: break-all;
}

/* API keys table */
.api-keys-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--space-m);
}

.api-keys-table th,
.api-keys-table td {
  padding: var(--space-2xs) var(--space-xs);
  text-align: left;
  border-bottom: 1px solid var(--clr-gray-700);
}

.api-keys-table th {
  color: var(--clr-gray-400);
  font-weight: 600;
}

.status--active {
  color: var(--clr-primary-400);
}

.status--revoked {
  color: var(--clr-gray-500);
}

/* API key create form */
.api-key-form {
  margin-top: var(--space-s);
}

.api-key-form__row {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-2xs);
}

.api-key-form__row input {
  flex: 1;
}

/* Button variants */
.button--small {
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-300);
}

.button--danger {
  background: var(--clr-gray-700);
  color: #e74c3c;
}

.button--danger:hover {
  background: #e74c3c;
  color: white;
}
</style>
