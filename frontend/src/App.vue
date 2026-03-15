<template>
  <div class="app">
    <AppSidebar
      :open="sidebarOpen"
      @toggle="sidebarOpen = !sidebarOpen"
    />
    <div
      class="layout"
      :class="{ 'layout--expanded': !sidebarOpen }"
    >
      <main class="main">
        <RouterView />
      </main>
    </div>
    <SubmitIssueButton @click="issueModalOpen = true" />
    <SubmitIssueModal
      :visible="issueModalOpen"
      @close="issueModalOpen = false"
    />
    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import SubmitIssueButton from '@/components/SubmitIssueButton.vue'
import SubmitIssueModal from '@/components/SubmitIssueModal.vue'
import NotificationToast from '@/components/NotificationToast.vue'
import { useTheme } from '@/composables/useTheme'

useTheme()

const sidebarOpen = ref(true)
const issueModalOpen = ref(false)
</script>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
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
