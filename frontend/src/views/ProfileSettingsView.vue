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
            <div class="hue-slider__swatches">
              <div
                class="hue-slider__swatch"
                :style="{ background: `oklch(0.75 0.157 ${accentHue})` }"
                title="Accent"
              ></div>
              <div
                class="hue-slider__swatch hue-slider__swatch--companion"
                :style="{ background: secondaryPreview }"
                title="Secondary"
              ></div>
              <div
                class="hue-slider__swatch hue-slider__swatch--companion"
                :style="{ background: tertiaryPreview }"
                title="Tertiary"
              ></div>
              <div
                class="hue-slider__swatch hue-slider__swatch--companion"
                :style="{ background: infoPreview }"
                title="Info"
              ></div>
              <div
                class="hue-slider__swatch hue-slider__swatch--companion"
                :style="{ background: subtlePreview }"
                title="Subtle"
              ></div>
            </div>
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

      <!-- Sidebar Order -->
      <div class="grid__item">
        <h3>Sidebar Order</h3>
        <p class="setting-description">Drag to reorder the sidebar navigation links.</p>
        <draggable
          :list="sidebarLinks"
          item-key="to"
          handle=".sidebar-order__drag-handle"
          ghost-class="sidebar-order__ghost"
          :animation="150"
          class="sidebar-order"
          @end="onSidebarDragEnd"
        >
          <template #item="{ element: link }">
            <div class="sidebar-order__item">
              <div class="sidebar-order__drag-handle">
                <i class="fa-solid fa-grip-vertical"></i>
              </div>
              <i
                :class="link.icon"
                class="sidebar-order__icon"
              ></i>
              <span class="sidebar-order__label">{{ link.label }}</span>
            </div>
          </template>
        </draggable>
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
              <td>{{ formatDate(key.created_at, 'shortDate') }}</td>
              <td>{{ key.last_used_at ? formatDate(key.last_used_at, 'shortDate') : 'Never' }}</td>
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
import { allMainLinks, DEFAULT_SIDEBAR_ORDER, type NavLink } from '@/components/sidebarLinks'
import draggable from 'vuedraggable'
import ProfileSubnav from '@/components/ProfileSubnav.vue'
import { formatDate } from '@/composables/formatDate'

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
const baseHue = computed(() => {
  const t = themes.find((th) => th.id === selectedThemeColor.value)
  return t?.hue ?? 224
})
const secondaryPreview = computed(() => `oklch(0.65 0.12 ${(accentHue.value + 120) % 360})`)
const tertiaryPreview = computed(() => `oklch(0.65 0.10 ${(accentHue.value + 240) % 360})`)
const infoPreview = computed(() => `oklch(0.70 0.08 ${(accentHue.value + 180) % 360})`)
const subtlePreview = computed(() => `oklch(0.55 0.04 ${baseHue.value})`)
const availableFonts = [...fonts].sort((a, b) => a.name.localeCompare(b.name))
const keyName = ref('')
const newlyCreatedKey = ref<string | null>(null)

// Sidebar ordering — vuedraggable mutates sidebarLinks directly via :list
const sidebarLinks = ref<NavLink[]>([])

async function onSidebarDragEnd() {
  const order = sidebarLinks.value.map((link) => link.to)
  try {
    await auth.updatePreferences({ sidebar_order: order })
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update sidebar order: ${detail}`, 'error')
  }
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
    const order = (auth.preferences.sidebar_order as string[] | undefined) ?? DEFAULT_SIDEBAR_ORDER
    const linkMap = new Map(allMainLinks.map((link) => [link.to, link]))
    sidebarLinks.value = order.map((path) => linkMap.get(path)).filter((l): l is NavLink => l != null)
  } else {
    sidebarLinks.value = [...allMainLinks]
  }
})
</script>

<style lang="scss" scoped>
@use 'components/buttons';
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
  @include buttons.neu-button($active-class: '--selected', $hover-transform: scale(1.1), $pressed-transform: scale(0.98));
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
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

.hue-slider__swatches {
  display: flex;
  align-items: center;
  gap: var(--space-3xs);
}

.hue-slider__swatch {
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  border: 2px solid var(--clr-gray-600);
}

.hue-slider__swatch--companion {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 0.25rem;
  border-width: 1px;
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
  @include buttons.neu-button($active-class: '--selected', $hover-transform: scale(1.1), $pressed-transform: scale(0.98));
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-s) var(--space-m);
  min-height: 3.5rem;
  text-align: left;
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

/* Sidebar order */
.sidebar-order {
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
}

.sidebar-order__item {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-2xs) var(--space-s);
  border-radius: 0.375rem;
  box-shadow: var(--floating-box);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: var(--bubble-box);
  }
}

.sidebar-order__drag-handle {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  cursor: grab;
  color: var(--clr-gray-500);
  font-size: 0.75rem;
  opacity: 0.4;
  transition: opacity 0.15s ease;

  .sidebar-order__item:hover & {
    opacity: 1;
  }

  &:active {
    cursor: grabbing;
  }
}

.sidebar-order__icon {
  width: 1.25em;
  text-align: center;
  flex-shrink: 0;
  color: var(--clr-accent);
}

.sidebar-order__label {
  flex: 1;
  font-weight: 500;
}

.sidebar-order__ghost {
  opacity: 0.3;
}
</style>
