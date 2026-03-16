<template>
  <div class="grid grid--one-column">
    <h1>Admin</h1>
    <AdminSubnav :active="activeTab" />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminSubnav from '@/components/AdminSubnav.vue'

const route = useRoute()

const activeTab = computed(() => {
  const name = route.name as string
  if (name === 'admin-scheduler') return 'scheduler'
  if (name === 'admin-users') return 'users'
  if (name === 'admin-config') return 'config'
  if (name === 'admin-smoke') return 'smoke'
  if (name === 'admin-design') return 'design'
  return 'system'
})
</script>
