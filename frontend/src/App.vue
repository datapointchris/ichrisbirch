<template>
  <div
    class="app"
    :class="{ 'app--loading': !ready }"
  >
    <AppSidebar
      :open="sidebarOpen"
      @toggle="sidebarOpen = !sidebarOpen"
      @open-issue="issueModalOpen = true"
    />
    <div
      class="layout"
      :class="{ 'layout--expanded': !sidebarOpen }"
    >
      <main class="main">
        <RouterView v-if="ready" />
      </main>
    </div>
    <SubmitIssueModal
      :visible="issueModalOpen"
      @close="issueModalOpen = false"
    />
    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import SubmitIssueModal from '@/components/SubmitIssueModal.vue'
import NotificationToast from '@/components/NotificationToast.vue'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'

useTheme()

const auth = useAuthStore()
const sidebarOpen = ref(true)
const issueModalOpen = ref(false)
const ready = ref(false)

onMounted(async () => {
  try {
    await auth.fetchCurrentUser()
  } catch {
    // Auth failure is non-fatal — user just won't see admin features
  }
  ready.value = true
  // Clear the pre-load dark background so theme colors show through
  document.body.style.background = ''
})
</script>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
}

.app--loading {
  visibility: hidden;
}

.layout {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.25s ease;
}

.layout--expanded {
  margin-left: 0;
}

.main {
  flex: 1;
  padding: var(--space-m);
}
</style>
