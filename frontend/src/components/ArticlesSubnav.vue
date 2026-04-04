<template>
  <AppSubnav :links="links">
    <button
      data-testid="article-add-button"
      class="button"
      @click="showModal = true"
    >
      <span class="button__text">Add Article</span>
    </button>
  </AppSubnav>

  <AddEditArticleModal
    :visible="showModal"
    :edit-data="null"
    @close="showModal = false"
    @create="handleCreate"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { ArticleCreate } from '@/api/client'
import AppSubnav from '@/components/AppSubnav.vue'
import { ARTICLES_SUBNAV } from '@/config/subnavLinks'
import AddEditArticleModal from '@/components/articles/AddEditArticleModal.vue'

const links = ARTICLES_SUBNAV

const store = useArticlesStore()
const { show: notify } = useNotifications()
const showModal = ref(false)

async function handleCreate(data: ArticleCreate) {
  try {
    await store.create(data)
    notify(`${data.title} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add article: ${detail}`, 'error')
  }
}
</script>
