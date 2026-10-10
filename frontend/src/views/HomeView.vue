<template>
  <div class="main-index-content">
    <h1>Chris Birch</h1>
    <h2>Data Engineer</h2>
    <p class="home-tagline">
      <span class="home-tagline__text">Nothing Is Truly Gone</span>
      <code class="home-tagline__cmd">git log --all --full-history</code>
    </p>
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
import { PROJECT_LINKS, SERVICE_LINKS } from '@/config/homeLinks'

const authStore = useAuthStore()

const allLinks = computed(() => (authStore.isAdmin ? [...PROJECT_LINKS, ...SERVICE_LINKS] : PROJECT_LINKS))
</script>
