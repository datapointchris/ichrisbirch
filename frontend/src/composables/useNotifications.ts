import { ref } from 'vue'

export interface Notification {
  id: number
  message: string
  category: 'success' | 'warning' | 'error'
  closing: boolean
}

let nextId = 0

const notifications = ref<Notification[]>([])

export function useNotifications() {
  function show(message: string, category: Notification['category'] = 'success') {
    const notification: Notification = {
      id: nextId++,
      message,
      category,
      closing: false,
    }
    notifications.value.push(notification)
  }

  function close(id: number) {
    const notification = notifications.value.find((n) => n.id === id)
    if (notification) {
      notification.closing = true
      setTimeout(() => {
        notifications.value = notifications.value.filter((n) => n.id !== id)
      }, 1000)
    }
  }

  return {
    notifications,
    show,
    close,
  }
}
