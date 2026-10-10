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
      v-if="isPhone && sidebarOpen"
      class="sidebar-backdrop"
      data-testid="sidebar-backdrop"
      @click="sidebarOpen = false"
    ></div>
    <div
      class="layout"
      :class="{ 'layout--expanded': !sidebarOpen || isPhone }"
    >
      <header
        v-if="isPhone"
        class="phone-bar"
        data-testid="phone-bar"
      >
        <div
          class="button-sidebar-tab"
          data-testid="sidebar-open-button"
          role="button"
          aria-label="Open the menu"
          tabindex="0"
          @click="sidebarOpen = true"
          @keydown.enter="sidebarOpen = true"
        >
          <div class="button-sidebar-tab__text">
            <span class="fa-solid fa-bars"></span>
          </div>
        </div>
      </header>
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
import { onMounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import SubmitIssueModal from '@/components/SubmitIssueModal.vue'
import NotificationToast from '@/components/NotificationToast.vue'
import { useTheme } from '@/composables/useTheme'
import { useDisplayZone } from '@/composables/displayZone'
import { usePhoneViewport } from '@/composables/usePhoneViewport'
import { useAuthStore } from '@/stores/auth'

useTheme()
useDisplayZone()

const auth = useAuthStore()
const route = useRoute()
// On a phone the sidebar covers the page, so it starts closed and closes again
// once a link in it has been followed.
const isPhone = usePhoneViewport()
const sidebarOpen = ref(!isPhone.value)
const issueModalOpen = ref(false)
const ready = ref(false)

watch(isPhone, (phone) => {
  sidebarOpen.value = !phone
})

watch(
  () => route.fullPath,
  () => {
    if (isPhone.value) sidebarOpen.value = false
  }
)

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

<style lang="scss" scoped>
@use 'abstracts/breakpoints';

.app {
  display: flex;
  min-height: 100vh;
}

.app--loading {
  visibility: hidden;
}

.layout {
  flex: 1;
  min-width: 0;
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
  padding-top: calc(var(--space-m) + env(safe-area-inset-top));
  padding-bottom: calc(var(--space-m) + env(safe-area-inset-bottom));

  @include breakpoints.phone {
    padding-top: var(--space-s);
    padding-left: calc(var(--space-xs) + env(safe-area-inset-left));
    padding-right: calc(var(--space-xs) + env(safe-area-inset-right));
  }
}

// The phone bar takes the notch, so the page under it needs no inset of its own.
.phone-bar {
  position: sticky;
  top: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  height: calc(var(--phone-bar-height) + env(safe-area-inset-top));
  padding: env(safe-area-inset-top) calc(var(--space-xs) + env(safe-area-inset-right)) 0 calc(var(--space-xs) + env(safe-area-inset-left));
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 99;
}
</style>
