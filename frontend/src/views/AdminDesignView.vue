<template>
  <div class="design-page">
    <!-- Theme switcher -->
    <div class="theme-switcher">
      <button
        v-for="theme in allThemes"
        :key="theme.id"
        class="theme-switcher__btn"
        :class="{ 'theme-switcher__btn--active': currentTheme === theme.id }"
        :style="{ background: theme.swatch }"
        :title="theme.name"
        @click="switchTheme(theme.id)"
      >
        {{ theme.name }}
      </button>
    </div>

    <!-- Shadow style columns -->
    <div class="style-columns">
      <div
        v-for="style in shadowStyles"
        :key="style.name"
        class="style-col"
      >
        <h3 class="style-col__title">{{ style.name }}</h3>

        <!-- Swatch grid spaced -->
        <div class="swatch-grid swatch-grid--spaced">
          <button
            v-for="n in 6"
            :key="'spaced-' + n"
            class="swatch-btn"
            :class="[style.baseClass, { [style.pressedClass]: pressedButtons[style.name + '-spaced-' + n] }]"
            @click="togglePressed(style.name + '-spaced-' + n)"
          >
            {{ n }}
          </button>
        </div>

        <!-- Swatch grid tight -->
        <div class="swatch-grid swatch-grid--tight">
          <button
            v-for="n in 6"
            :key="'tight-' + n"
            class="swatch-btn"
            :class="[style.baseClass, { [style.pressedClass]: pressedButtons[style.name + '-tight-' + n] }]"
            @click="togglePressed(style.name + '-tight-' + n)"
          >
            {{ n }}
          </button>
        </div>

        <!-- Sidebar-style nav links -->
        <div class="nav-list">
          <button
            v-for="link in navLinks"
            :key="link.label"
            class="nav-btn"
            :class="[style.baseClass, { [style.pressedClass]: pressedButtons[style.name + '-nav-' + link.label] }]"
            @click="togglePressed(style.name + '-nav-' + link.label)"
          >
            <i :class="link.icon"></i>
            <span>{{ link.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Segmented toggle experiments -->
    <h3 class="style-col__title">Segmented Toggle Groups</h3>
    <div class="segment-experiments">
      <div
        v-for="experiment in segmentExperiments"
        :key="experiment.name"
        class="segment-experiment"
      >
        <h4 class="segment-experiment__title">{{ experiment.name }}</h4>
        <div
          class="segment-experiment__group"
          :class="experiment.containerClass"
          role="radiogroup"
        >
          <button
            v-for="opt in segmentOptions"
            :key="opt"
            role="radio"
            :aria-checked="segmentSelections[experiment.name] === opt"
            class="segment-experiment__option"
            :class="[experiment.buttonClass, { [experiment.selectedClass]: segmentSelections[experiment.name] === opt }]"
            @click="segmentSelections[experiment.name] = opt"
          >
            {{ opt }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { applyTheme, themes } from '@/composables/useTheme'

const allThemes = themes
const currentTheme = ref('turquoise')
const pressedButtons = reactive<Record<string, boolean>>({})

function switchTheme(themeId: string) {
  currentTheme.value = themeId
  applyTheme(themeId)
}

function togglePressed(key: string) {
  pressedButtons[key] = !pressedButtons[key]
}

const shadowStyles = [
  { name: 'mixin: translate', baseClass: 'style--mixin-translate', pressedClass: 'style--mixin-translate--active' },
  { name: 'mixin: scale 1.2', baseClass: 'style--mixin-scale', pressedClass: 'style--mixin-scale--active' },
  { name: 'mixin: scale 1.1 left', baseClass: 'style--mixin-left', pressedClass: 'style--mixin-left--active' },
]

const navLinks = [
  { label: 'Articles', icon: 'fa-solid fa-newspaper' },
  { label: 'Books', icon: 'fa-solid fa-book' },
  { label: 'Events', icon: 'fa-solid fa-calendar' },
  { label: 'Habits', icon: 'fa-solid fa-repeat' },
  { label: 'Tasks', icon: 'fa-solid fa-list-check' },
]

const segmentOptions = ['Today', 'Yesterday', 'This Week', 'Last 7', 'This Month', 'Last 30', 'This Year', 'All']

const segmentSelections = reactive<Record<string, string>>({
  'hover: color shift': 'This Week',
  'hover: inner glow': 'This Week',
  'hover: bg + text glow': 'This Week',
})

const segmentExperiments = [
  {
    name: 'hover: color shift',
    containerClass: 'seg-group--dark-shadow',
    buttonClass: 'seg-btn--color-shift',
    selectedClass: 'seg-btn--color-shift--selected',
  },
  {
    name: 'hover: inner glow',
    containerClass: 'seg-group--dark-shadow',
    buttonClass: 'seg-btn--inner-glow',
    selectedClass: 'seg-btn--inner-glow--selected',
  },
  {
    name: 'hover: bg + text glow',
    containerClass: 'seg-group--dark-shadow',
    buttonClass: 'seg-btn--text-glow',
    selectedClass: 'seg-btn--text-glow--selected',
  },
]
</script>

<style lang="scss" scoped>
@use 'components/buttons';
.design-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-l);
}

/* Theme switcher */
.theme-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3xs);
}

.theme-switcher__btn {
  padding: var(--space-2xs) var(--space-s);
  border-radius: var(--button-border-radius);
  cursor: pointer;
  font-size: var(--fs-300);
  font-weight: 500;
  color: var(--clr-gray-100);
  border: 2px solid transparent;
  transition: all 0.1s ease;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
}

.theme-switcher__btn:hover {
  transform: scale(1.05);
}

.theme-switcher__btn--active {
  border-color: var(--clr-gray-100);
}

/* Style columns */
.style-columns {
  display: flex;
  gap: var(--space-l);
}

.style-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
}

.style-col__title {
  font-size: var(--fs-200);
  color: var(--clr-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: center;
}

/* Swatch grids */
.swatch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.swatch-grid--spaced {
  gap: var(--space-xs);
}

.swatch-grid--tight {
  gap: var(--space-3xs);
}

.swatch-btn {
  padding: var(--space-xs) var(--space-s);
  border-radius: var(--button-border-radius);
  background-color: var(--clr-primary);
  color: var(--clr-gray-100);
  font-size: var(--fs-300);
  font-weight: 500;
  text-align: center;
  cursor: pointer;
}

/* Nav-style links */
.nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-3xs) var(--space-xs);
  border-radius: var(--button-border-radius);
  background-color: var(--clr-primary);
  color: var(--clr-gray-100);
  font-weight: 500;
  font-size: var(--fs-300);
  cursor: pointer;
}

.nav-btn i {
  width: 1.25em;
  text-align: center;
}

/* ── Segmented toggle experiments ── */
.segment-experiments {
  display: flex;
  flex-direction: column;
  gap: var(--space-l);
}

.segment-experiment {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.segment-experiment__title {
  font-size: var(--fs-200);
  color: var(--clr-gray-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.segment-experiment__group {
  display: inline-flex;
  border-radius: var(--button-border-radius);
  overflow: hidden;
  align-self: flex-start;
}

.seg-group--dark-shadow {
  box-shadow: var(--floating-box);
  background-color: var(--clr-primary--darker);
}

/* Shared base for all segment button experiments */
%seg-btn-base {
  background-color: var(--clr-primary);
  box-shadow: var(--neu-hover);
  color: var(--clr-gray-100);
  cursor: pointer;
  transition: all 0.1s ease;
  padding: var(--space-xs) var(--space-s);
  font-size: var(--fs-400);
  border: none;
  font-family: inherit;
  position: relative;
  z-index: 1;
}

%seg-btn-pressed {
  box-shadow: var(--neu-pressed);
  background-color: var(--clr-primary--darker);
  color: var(--clr-accent);
  z-index: 0;
}

/* 1. Color shift — lighter bg + accent text, no shadow change */
.seg-btn--color-shift {
  @extend %seg-btn-base;

  &:hover:not(.seg-btn--color-shift--selected) {
    background-color: var(--clr-primary--lighter);
    color: var(--clr-accent);
  }

  &--selected {
    @extend %seg-btn-pressed;
  }
}

/* 2. Inner glow — accent-tinted inset glow + text scale + press animation */
.seg-btn--inner-glow {
  @extend %seg-btn-base;
  transition:
    color 0.15s ease,
    font-size 0.15s ease,
    background-color 0.15s ease;

  &:hover:not(.seg-btn--inner-glow--selected) {
    color: var(--clr-accent);
    box-shadow:
      var(--neu-hover),
      inset 0 0 16px var(--clr-accent-dark);
    font-size: calc(var(--fs-400) * 1.2);
  }

  &--selected {
    @extend %seg-btn-pressed;
    animation: segment-press 0.5s ease-in-out;
  }
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

/* 3. Background + text glow — lighter bg + glowing text shadow */
.seg-btn--text-glow {
  @extend %seg-btn-base;

  &:hover:not(.seg-btn--text-glow--selected) {
    background-color: var(--clr-primary--lighter);
    color: var(--clr-accent);
    text-shadow:
      0 0 8px var(--clr-accent),
      0 0 20px var(--clr-accent-dark);
  }

  &--selected {
    @extend %seg-btn-pressed;
  }
}

/* ── Column 1: translate, press scale 0.99 ── */
.style--mixin-translate {
  @include buttons.neu-button($active-class: '--active', $hover-transform: translateY(-2px), $pressed-transform: scale(0.99));
}

/* ── Column 2: scale 1.2, press scale 0.98 ── */
.style--mixin-scale {
  @include buttons.neu-button($active-class: '--active', $hover-transform: scale(1.2), $pressed-transform: scale(0.98));
}

/* ── Column 3: scale 1.3 center left, press scale 0.99 ── */
.style--mixin-left {
  @include buttons.neu-button($active-class: '--active', $hover-transform: scale(1.3), $pressed-transform: scale(0.99));
  transform-origin: center left;
}
</style>
