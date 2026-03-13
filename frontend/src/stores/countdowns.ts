import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import type { Countdown, CountdownCreate, CountdownUpdate } from '@/api/client'

export const useCountdownsStore = defineStore('countdowns', () => {
  const countdowns = ref<Countdown[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const sortedCountdowns = computed(() => [...countdowns.value].sort((a, b) => a.due_date.localeCompare(b.due_date)))

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Countdown[]>('/countdowns/')
      countdowns.value = response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch countdowns'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function create(input: CountdownCreate) {
    const response = await api.post<Countdown>('/countdowns/', input)
    countdowns.value.push(response.data)
    return response.data
  }

  async function update(id: number, input: CountdownUpdate) {
    const response = await api.patch<Countdown>(`/countdowns/${id}/`, input)
    const index = countdowns.value.findIndex((c) => c.id === id)
    if (index !== -1) {
      countdowns.value[index] = response.data
    }
    return response.data
  }

  async function remove(id: number) {
    await api.delete(`/countdowns/${id}/`)
    countdowns.value = countdowns.value.filter((c) => c.id !== id)
  }

  return {
    countdowns,
    loading,
    error,
    sortedCountdowns,
    fetchAll,
    create,
    update,
    remove,
  }
})
