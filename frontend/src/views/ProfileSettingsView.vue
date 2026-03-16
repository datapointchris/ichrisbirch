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

        <label class="section-label">Theme</label>
        <div class="theme-selector">
          <div class="theme-selector__group">
            <span class="theme-selector__group-label">Colors</span>
            <div class="theme-colors">
              <button
                v-for="theme in colorThemes"
                :key="theme.id"
                class="theme-colors__swatch"
                :class="{ 'theme-colors__swatch--selected': selectedThemeColor === theme.id }"
                :style="{ background: theme.swatch }"
                :title="theme.name"
                @click="selectThemeColor(theme.id)"
              >
                <span class="theme-colors__label">{{ theme.name }}</span>
              </button>
            </div>
          </div>
          <div class="theme-selector__group">
            <span class="theme-selector__group-label">Named Themes</span>
            <div class="theme-colors">
              <button
                v-for="theme in namedThemes"
                :key="theme.id"
                class="theme-colors__swatch theme-colors__swatch--named"
                :class="{ 'theme-colors__swatch--selected': selectedThemeColor === theme.id }"
                :style="{ background: theme.swatch }"
                :title="theme.name"
                @click="selectThemeColor(theme.id)"
              >
                <span class="theme-colors__label">{{ theme.name }}</span>
              </button>
            </div>
          </div>
        </div>

        <div
          class="setting-row"
          :class="{ 'setting-row--disabled': !isColorTheme }"
        >
          <label class="setting-row__label">Accent Color</label>
          <div class="hue-slider">
            <input
              type="range"
              min="0"
              max="360"
              :value="accentHue"
              class="hue-slider__input"
              @input="onAccentHueInput"
              @change="saveAccentHue"
            />
            <div
              class="hue-slider__preview"
              :style="{ background: `oklch(0.75 0.157 ${accentHue})` }"
            ></div>
            <span class="hue-slider__value">{{ accentHue }}°</span>
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

        <label class="section-label">Font</label>
        <div class="font-selector">
          <button
            v-for="font in availableFonts"
            :key="font.id"
            class="font-selector__option"
            :class="{
              'font-selector__option--selected': selectedFont === font.id,
              'font-selector__option--mono': font.category === 'monospace',
              'font-selector__option--sans': font.category === 'sans-serif',
            }"
            :style="{ fontFamily: font.family }"
            @click="selectFont(font.id)"
          >
            <span class="font-selector__name">{{ font.name }}</span>
            <span class="font-selector__preview">The quick brown fox jumps over the lazy dog</span>
            <span class="font-selector__tag">{{ font.category === 'monospace' ? 'mono' : 'sans' }}</span>
          </button>
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { applyTheme, applyFont, applyAccentHue, fonts, themes } from '@/composables/useTheme'
import { ApiError } from '@/api/errors'
import ProfileSubnav from '@/components/ProfileSubnav.vue'

const auth = useAuthStore()
const { show: notify } = useNotifications()

const colorThemes = themes.filter((t) => t.type === 'color')
const namedThemes = themes.filter((t) => t.type === 'named')

const selectedThemeColor = ref(auth.preferences?.theme_color ?? 'turquoise')
const darkMode = ref(auth.preferences?.dark_mode ?? true)
const selectedFont = ref((auth.preferences?.font_family as string) ?? 'ubuntu-mono')
const accentHue = ref(Number(auth.preferences?.custom_accent_hue) || 62)
const isColorTheme = computed(() => {
  const t = themes.find((th) => th.id === selectedThemeColor.value)
  return t?.type === 'color' && t.id !== 'random'
})
const availableFonts = [...fonts].sort((a, b) => a.name.localeCompare(b.name))
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

async function selectThemeColor(themeId: string) {
  selectedThemeColor.value = themeId
  applyTheme(themeId)
  try {
    await auth.updatePreferences({ theme_color: themeId })
    const theme = themes.find((t) => t.id === themeId)
    notify(`Theme set to ${theme?.name ?? themeId}`, 'success')
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

function onAccentHueInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  accentHue.value = value
  applyAccentHue(value)
}

async function saveAccentHue() {
  try {
    await auth.updatePreferences({ custom_accent_hue: accentHue.value })
    notify(`Accent color updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update accent: ${detail}`, 'error')
  }
}

async function selectFont(fontId: string) {
  selectedFont.value = fontId
  applyFont(fontId)
  try {
    await auth.updatePreferences({ font_family: fontId })
    const font = availableFonts.find((f) => f.id === fontId)
    notify(`Font set to ${font?.name ?? fontId}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update font: ${detail}`, 'error')
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
    if (auth.preferences.font_family) {
      selectedFont.value = auth.preferences.font_family as string
    }
    if (auth.preferences.custom_accent_hue) {
      accentHue.value = Number(auth.preferences.custom_accent_hue)
    }
  }
})
</script>

<style scoped>
.setting-row {
  display: flex;
  align-items: center;
  gap: var(--space-m);
  margin-top: var(--space-s);
  margin-bottom: var(--space-s);
}

.section-label {
  display: block;
  font-size: var(--fs-500);
  font-weight: 700;
  color: var(--clr-gray-300);
  margin-top: var(--space-m);
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xs);
}

.theme-colors__swatch {
  height: 3rem;
  border-radius: var(--button-border-radius);
  background-color: var(--clr-primary);
  box-shadow: var(--floating-box);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.theme-colors__swatch:hover:not(.theme-colors__swatch--selected) {
  box-shadow: var(--bubble-box);
  transform: scale(1.05);
}

.theme-colors__swatch--selected {
  box-shadow: var(--floating-box-pressed);
}

.theme-colors__label {
  font-size: var(--fs-400);
  color: var(--clr-gray-100);
  font-weight: 500;
  text-transform: capitalize;
}

.theme-colors__swatch--named {
  padding: var(--space-3xs) var(--space-2xs);
}

/* Hue slider */
.hue-slider {
  display: flex;
  align-items: center;
  gap: var(--space-s);
}

.hue-slider__input {
  width: 16rem;
  height: 0.5rem;
  appearance: none;
  border-radius: 0.25rem;
  background: linear-gradient(
    to right,
    oklch(0.75 0.157 0),
    oklch(0.75 0.157 60),
    oklch(0.75 0.157 120),
    oklch(0.75 0.157 180),
    oklch(0.75 0.157 240),
    oklch(0.75 0.157 300),
    oklch(0.75 0.157 360)
  );
  cursor: pointer;
}

.hue-slider__input::-webkit-slider-thumb {
  appearance: none;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: white;
  border: 2px solid var(--clr-gray-600);
  cursor: grab;
}

.hue-slider__preview {
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  border: 2px solid var(--clr-gray-600);
}

.hue-slider__value {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  min-width: 3rem;
}

/* Theme selector layout */
.theme-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-m);
}

.theme-selector__group-label {
  font-size: var(--fs-200);
  color: var(--clr-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3xs);
  display: block;
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

/* Setting row vertical alignment variant */
.setting-row--top {
  align-items: flex-start;
}

.setting-row--disabled {
  opacity: 0.35;
  pointer-events: none;
}

/* Font selector */
.font-selector {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
}

.font-selector__option {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-s) var(--space-m);
  min-height: 3.5rem;
  border-radius: var(--button-border-radius);
  background-color: var(--clr-primary);
  box-shadow: var(--floating-box);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  color: var(--clr-gray-100);
}

.font-selector__option:hover:not(.font-selector__option--selected) {
  box-shadow: var(--bubble-box);
  transform: scale(1.02);
}

.font-selector__option--selected {
  box-shadow: var(--floating-box-pressed);
  background-color: var(--clr-primary--darker);
  color: var(--clr-accent);
}

.font-selector__name {
  font-weight: 700;
  min-width: 9rem;
  color: var(--clr-gray-100);
  font-size: var(--fs-400);
}

.font-selector__preview {
  flex: 1;
  font-size: var(--fs-400);
  color: var(--clr-gray-400);
}

.font-selector__tag {
  font-size: var(--fs-200);
  color: var(--clr-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
