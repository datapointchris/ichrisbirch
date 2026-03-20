<template>
  <div class="grid grid--one-column grid--tight">
    <div class="tasks-subnav">
      <RouterLink
        to="/tasks"
        class="tasks-subnav__link"
        :class="{ 'tasks-subnav__link--active': active === 'priority' }"
      >
        Priority Tasks
      </RouterLink>
      <RouterLink
        to="/tasks/todo"
        class="tasks-subnav__link"
        :class="{ 'tasks-subnav__link--active': active === 'todo' }"
      >
        Outstanding Tasks
      </RouterLink>
      <RouterLink
        to="/tasks/completed"
        class="tasks-subnav__link"
        :class="{ 'tasks-subnav__link--active': active === 'completed' }"
      >
        Completed Tasks
      </RouterLink>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

defineProps<{
  active: 'priority' | 'todo' | 'completed' | 'search'
}>()

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

<style scoped>
.tasks-subnav {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.tasks-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.tasks-subnav__link:hover {
  color: var(--clr-primary-400);
}

.tasks-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
