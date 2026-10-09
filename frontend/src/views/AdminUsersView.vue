<template>
  <div>
    <div class="admin-section">
      <h2>Signups</h2>
      <div
        v-if="store.settingsLoading"
        class="admin__empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.settings === null"
        class="admin__empty"
      >
        Signup state unavailable
      </div>
      <NeuToggleGroup
        v-else
        :model-value="signupState"
        :options="signupStateOptions"
        data-testid="admin-signups-toggle"
        @update:model-value="handleSignupStateChange"
      />
    </div>

    <div class="admin-section">
      <h2>Users</h2>
      <div
        v-if="store.usersLoading"
        class="admin__empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.users.length === 0"
        class="admin__empty"
      >
        No users found
      </div>
      <table
        v-else
        class="admin-table"
      >
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Admin</th>
            <th>Created</th>
            <th>Last Login</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in store.users"
            :key="user.id"
          >
            <td>{{ user.name }}</td>
            <td class="admin-table__mono">{{ user.email }}</td>
            <td>
              <label class="admin-toggle">
                <input
                  type="checkbox"
                  :checked="user.is_admin"
                  :disabled="isSelf(user.id)"
                  @change="handleToggleAdmin(user)"
                />
                <span class="admin-toggle__label">
                  {{ user.is_admin ? 'Yes' : 'No' }}
                </span>
                <span
                  v-if="isSelf(user.id)"
                  class="admin-toggle__hint"
                  >(you)</span
                >
              </label>
            </td>
            <td>{{ formatDate(user.created_on, 'shortDate') }}</td>
            <td>{{ user.last_login ? formatDate(user.last_login, 'shortDate') : 'Never' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="store.error"
      class="admin-error"
    >
      {{ store.error.userMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { formatDate } from '@/composables/formatDate'
import { ApiError } from '@/api/errors'
import NeuToggleGroup from '@/components/NeuToggleGroup.vue'
import type { NeuToggleGroupOption } from '@/components/NeuToggleGroup.vue'
import type { User } from '@/api/client'

type SignupState = 'open' | 'closed'

const signupStateOptions: NeuToggleGroupOption<SignupState>[] = [
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
]

const store = useAdminStore()
const authStore = useAuthStore()
const { show: notify } = useNotifications()

const signupState = computed<SignupState>(() => (store.settings?.is_signup_open ? 'open' : 'closed'))

onMounted(() => {
  store.fetchSettings()
  store.fetchUsers()
})

async function handleSignupStateChange(state: SignupState) {
  if (state === signupState.value) return
  try {
    await store.updateSettings({ is_signup_open: state === 'open' })
    notify(`Signups are now ${state}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to set signups ${state}: ${detail}`, 'error')
  }
}

function isSelf(userId: number): boolean {
  return authStore.user?.id === userId
}

async function handleToggleAdmin(user: User) {
  const newValue = !user.is_admin
  try {
    await store.updateUserAdmin(user.id, newValue)
    notify(`${user.name} is ${newValue ? 'now' : 'no longer'} an admin`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update ${user.name}: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.admin-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  cursor: pointer;
}

.admin-toggle input:disabled {
  cursor: not-allowed;
}

.admin-toggle__hint {
  color: var(--clr-gray-500);
  font-size: var(--fs-300);
  font-style: italic;
}
</style>
