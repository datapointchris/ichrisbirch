<template>
  <div class="grid grid--one-column">
    <h1>Admin</h1>
    <AppSubnav :links="subnavLinks" />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import AppSubnav from '@/components/AppSubnav.vue'
import { ADMIN_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = ADMIN_SUBNAV
</script>
