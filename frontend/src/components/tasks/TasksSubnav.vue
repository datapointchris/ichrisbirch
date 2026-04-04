<template>
  <AppSubnav :links="links">
    <form
      class="task-search-form"
      @submit.prevent="onSearch"
    >
      <input
        v-model="searchTerms"
        data-testid="task-search-input"
        type="text"
        class="textbox"
        placeholder="Search tasks..."
      />
      <button
        type="submit"
        data-testid="task-search-button"
        class="button"
      >
        <span class="button__text">Search</span>
      </button>
    </form>
    <button
      data-testid="task-add-button"
      class="button"
      @click="$emit('add-task')"
    >
      <span class="button__text">Add Task</span>
    </button>
  </AppSubnav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppSubnav from '@/components/AppSubnav.vue'
import { TASKS_SUBNAV } from '@/config/subnavLinks'

const links = TASKS_SUBNAV

defineEmits<{
  'add-task': []
}>()

const router = useRouter()
const searchTerms = ref('')

function onSearch() {
  if (searchTerms.value.trim()) {
    router.push({ name: 'tasks-search', query: { q: searchTerms.value.trim() } })
  }
}
</script>
