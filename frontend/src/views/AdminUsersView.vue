<template>
  <div>
    <div class="admin-section">
      <h2>Users</h2>
      <div
        v-if="store.usersLoading"
        class="admin-empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.users.length === 0"
        class="admin-empty"
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
            <td>{{ formatDate(user.created_on) }}</td>
            <td>{{ user.last_login ? formatDate(user.last_login) : 'Never' }}</td>
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
import { onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { User } from '@/api/client'

const store = useAdminStore()
const authStore = useAuthStore()
const { show: notify } = useNotifications()

onMounted(() => {
  store.fetchUsers()
})

function isSelf(userId: number): boolean {
  return authStore.user?.id === userId
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
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
