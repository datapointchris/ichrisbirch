<template>
  <div
    role="radiogroup"
    class="neu-toggle-group"
    :data-testid="dataTestid"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="radio"
      :aria-checked="modelValue === opt.value"
      class="neu-toggle-group__option"
      :class="{ 'neu-toggle-group__option--selected': modelValue === opt.value }"
      :data-testid="dataTestid ? `${dataTestid}-option-${opt.value}` : undefined"
      @click="emit('update:modelValue', opt.value)"
    >
      <slot
        name="option"
        :option="opt"
      >
        {{ opt.label }}
      </slot>
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
export interface NeuToggleGroupOption<V = string | number> {
  value: V
  label: string
}

defineProps<{
  modelValue: T
  options: NeuToggleGroupOption<T>[]
  dataTestid?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()
</script>

<style scoped>
.neu-toggle-group {
  display: inline-flex;
  border-radius: var(--button-border-radius);
  box-shadow: var(--floating-box);
  background-color: var(--clr-primary--darker);
  overflow: hidden;
}

.neu-toggle-group__option {
  background-color: var(--clr-primary);
  box-shadow: var(--neu-hover);
  color: var(--clr-gray-100);
  cursor: pointer;
  transition:
    color 0.15s ease,
    font-size 0.15s ease,
    background-color 0.15s ease;
  padding: var(--space-xs) var(--space-s);
  font-size: var(--fs-400);
  border: none;
  font-family: inherit;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.neu-toggle-group__option:hover:not(.neu-toggle-group__option--selected) {
  color: var(--clr-accent);
  box-shadow:
    var(--neu-hover),
    inset 0 0 16px var(--clr-accent-dark);
  font-size: calc(var(--fs-400) * 1.2);
}

.neu-toggle-group__option--selected {
  box-shadow: var(--neu-pressed);
  background-color: var(--clr-primary--darker);
  color: var(--clr-accent);
  z-index: 0;
  animation: segment-press 0.5s ease-in-out;
}

@keyframes segment-press {
  0% {
    transform: scale(1);
  }
  35% {
    transform: scale(0.94);
  }
  100% {
    transform: scale(1);
  }
}
</style>
