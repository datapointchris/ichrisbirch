<template>
  <div class="main-index-content">
    <h1>Chris Birch</h1>
    <h2>Data Engineer</h2>
    <div class="home-links">
      <a
        v-for="link in allLinks"
        :key="link.label"
        :href="link.url"
        target="_blank"
      >
        <div class="home-link-button">
          <span class="home-link-label">{{ link.label }}</span>
          <i
            :class="link.icon"
            class="home-link-icon fa-2xl"
          ></i>
        </div>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface HomeLink {
  label: string
  url: string
  icon: string
}

const authStore = useAuthStore()

const projectLinks: HomeLink[] = [
  { label: 'Code', url: 'https://github.com/datapointchris/ichrisbirch', icon: 'fa-brands fa-github' },
  { label: 'Chat', url: 'https://chat.ichrisbirch.com', icon: 'fa-regular fa-message' },
  { label: 'API', url: 'https://api.ichrisbirch.com', icon: 'fa-solid fa-server' },
  { label: 'Docs', url: 'https://docs.ichrisbirch.com', icon: 'fa-regular fa-folder-open' },
]

const serviceLinks: HomeLink[] = [
  { label: 'Monitor', url: 'https://monitor.ichrisbirch.com', icon: 'fa-solid fa-chart-line' },
  { label: 'Files', url: 'https://files.ichrisbirch.com', icon: 'fa-solid fa-hard-drive' },
  { label: 'Vault', url: 'https://vault.ichrisbirch.com', icon: 'fa-solid fa-shield-halved' },
  { label: 'Photos', url: 'https://photos.ichrisbirch.com', icon: 'fa-solid fa-images' },
  { label: 'RSS', url: 'https://rss.ichrisbirch.com', icon: 'fa-solid fa-rss' },
  { label: 'Auth', url: 'https://auth.ichrisbirch.com', icon: 'fa-solid fa-lock' },
  { label: 'Learning', url: 'https://learning.ichrisbirch.com', icon: 'fa-solid fa-graduation-cap' },
]

const allLinks = computed(() => (authStore.isAdmin ? [...projectLinks, ...serviceLinks] : projectLinks))
</script>
