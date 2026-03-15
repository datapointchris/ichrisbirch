<template>
  <ProfileSubnav active="profile" />

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
      Unable to load profile.
    </div>
    <template v-else>
      <div class="grid__item">
        <h1>{{ auth.user.name }}</h1>
        <h2>Profile</h2>
        <dl class="profile-info">
          <dt>Name</dt>
          <dd>{{ auth.user.name }}</dd>
          <dt>Email</dt>
          <dd>{{ auth.user.email }}</dd>
          <dt>Role</dt>
          <dd>{{ auth.user.is_admin ? 'Admin' : 'User' }}</dd>
          <dt>Member Since</dt>
          <dd>{{ formatDate(auth.user.created_on) }}</dd>
          <dt>Last Login</dt>
          <dd>{{ auth.user.last_login ? formatDate(auth.user.last_login) : 'Never' }}</dd>
        </dl>
      </div>

      <div
        v-if="auth.preferences"
        class="grid__item"
      >
        <h3>Preferences</h3>
        <dl class="profile-info">
          <dt>Theme Color</dt>
          <dd>{{ auth.preferences.theme_color }}</dd>
          <dt>Dark Mode</dt>
          <dd>{{ auth.preferences.dark_mode ? 'On' : 'Off' }}</dd>
          <dt>Notifications</dt>
          <dd>{{ auth.preferences.notifications ? 'On' : 'Off' }}</dd>
        </dl>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ProfileSubnav from '@/components/ProfileSubnav.vue'

const auth = useAuthStore()

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})

function formatDate(dateStr: string): string {
  return dateFormatter.format(new Date(dateStr))
}

onMounted(() => {
  if (!auth.user) {
    auth.fetchCurrentUser()
  }
})
</script>

<style scoped>
.profile-info {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-2xs) var(--space-m);
  margin-top: var(--space-s);
}

.profile-info dt {
  color: var(--clr-gray-400);
  font-weight: 600;
}

.profile-info dd {
  margin: 0;
  color: var(--clr-gray-200);
}
</style>
