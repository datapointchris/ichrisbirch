<template>
  <div class="app">
    <AppSidebar :open="sidebarOpen" />
    <div
      class="layout"
      :class="{ 'layout--expanded': !sidebarOpen }"
    >
      <header class="topbar">
        <button
          class="topbar__toggle"
          @click="sidebarOpen = !sidebarOpen"
        >
          <i class="fa-solid fa-bars"></i>
        </button>
        <div class="topbar__spacer"></div>
      </header>
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

.topbar {
  display: flex;
  align-items: center;
  padding: var(--space-2xs) var(--space-s);
  border-bottom: 1px solid var(--clr-gray-800);
  background-color: var(--clr-primary);
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar__toggle {
  background: none;
  border: none;
  color: var(--clr-gray-100);
  font-size: var(--fs-500);
  cursor: pointer;
  padding: var(--space-3xs) var(--space-2xs);
  border-radius: 4px;
}

.topbar__toggle:hover {
  background-color: var(--clr-primary--lighter);
}

.topbar__spacer {
  flex: 1;
}

.main {
  flex: 1;
  padding: var(--space-m);
}
</style>
