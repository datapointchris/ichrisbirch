<template>
  <Teleport to="body">
    <div
      v-if="notifications.length > 0"
      class="flash-messages"
    >
      <TransitionGroup
        name="notification"
        tag="div"
      >
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="flash-messages__message"
          :class="[`flash-messages__message--${notification.category}`, { 'flash-messages__message--closing': notification.closing }]"
        >
          {{ notification.message }}
          <button
            class="flash-messages__close-button"
            @click="close(notification.id)"
          >
            X
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useNotifications } from '@/composables/useNotifications'

const { notifications, close } = useNotifications()
</script>

<style scoped>
.flash-messages__message--closing {
  opacity: 0;
  transition: opacity 1s ease;
}

.notification-enter-active {
  transition: all 0.4s ease;
}

.notification-leave-active {
  transition: all 0.6s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
