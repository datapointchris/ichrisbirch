<template>
  <div class="projects-page">
    <!-- Left pane: project list -->
    <aside class="projects-page__sidebar">
      <div class="projects-page__sidebar-header">
        <h2>Projects</h2>
        <button
          data-testid="project-add-button"
          class="button button--small"
          @click="showProjectModal = true"
        >
          <span class="button__text"><i class="fa-solid fa-plus"></i></span>
        </button>
      </div>

      <div
        v-if="store.loading"
        class="projects-page__empty"
      >
        Loading...
      </div>
      <div
        v-else-if="store.sortedProjects.length === 0"
        class="projects-page__empty"
      >
        No projects yet
      </div>
      <draggable
        v-else
        :list="localProjects"
        item-key="id"
        handle=".projects-page__drag-handle"
        ghost-class="projects-page__ghost"
        :animation="150"
        class="projects-page__project-list"
        @end="onProjectDragEnd"
      >
        <template #item="{ element: project }">
          <div
            data-testid="project-item"
            class="projects-page__project"
            :class="{ 'projects-page__project--selected': project.id === store.selectedProjectId }"
            @click="selectProject(project.id)"
          >
            <div class="projects-page__drag-handle">
              <i class="fa-solid fa-grip-vertical"></i>
            </div>
            <span class="projects-page__project-name">{{ project.name }}</span>
            <span class="projects-page__project-count">{{ project.item_count }}</span>
            <div class="projects-page__project-actions">
              <button
                data-testid="project-edit-button"
                class="projects-page__action-btn"
                title="Edit project"
                @click.stop="openEditProject(project)"
              >
                <i class="fa-solid fa-pen"></i>
              </button>
              <button
                data-testid="project-delete-button"
                class="projects-page__action-btn projects-page__action-btn--danger"
                title="Delete project"
                @click.stop="handleDeleteProject(project.id)"
              >
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
          </div>
        </template>
      </draggable>
    </aside>

    <!-- Right pane: items for selected project -->
    <main class="projects-page__items">
      <div
        v-if="!store.selectedProjectId"
        class="projects-page__empty"
      >
        Select a project to view items
      </div>
      <template v-else>
        <div class="projects-page__items-header">
          <h2>{{ store.selectedProject?.name }}</h2>
          <button
            data-testid="project-item-add-button"
            class="button button--small"
            @click="showItemModal = true"
          >
            <span class="button__text"><i class="fa-solid fa-plus"></i> Add Item</span>
          </button>
        </div>

        <div
          v-if="store.itemsLoading"
          class="projects-page__empty"
        >
          Loading items...
        </div>
        <div
          v-else-if="store.sortedItems.length === 0"
          class="projects-page__empty"
        >
          No items in this project
        </div>
        <draggable
          v-else
          :list="localItems"
          item-key="id"
          handle=".projects-page__drag-handle"
          ghost-class="projects-page__ghost"
          :animation="150"
          class="projects-page__item-list"
          @end="onItemDragEnd"
        >
          <template #item="{ element: item }">
            <div
              data-testid="project-item-row"
              class="projects-page__item"
              :class="{
                'projects-page__item--completed': item.completed,
                'projects-page__item--archived': item.archived,
                'projects-page__item--blocked': isBlocked(item.id),
              }"
            >
              <div class="projects-page__drag-handle">
                <i class="fa-solid fa-grip-vertical"></i>
              </div>

              <button
                data-testid="project-item-complete-button"
                class="projects-page__check"
                :title="item.completed ? 'Mark incomplete' : 'Mark complete'"
                @click="handleToggleComplete(item)"
              >
                <i :class="item.completed ? 'fa-solid fa-circle-check' : 'fa-regular fa-circle'"></i>
              </button>

              <div class="projects-page__item-content">
                <span class="projects-page__item-title">{{ item.title }}</span>
                <span
                  v-if="item.notes"
                  class="projects-page__item-notes"
                >
                  {{ item.notes }}
                </span>
                <span
                  v-if="getBlockers(item.id).length > 0"
                  class="projects-page__item-blockers"
                >
                  <i class="fa-solid fa-lock"></i>
                  {{
                    getBlockers(item.id)
                      .map((b) => b.title)
                      .join(', ')
                  }}
                </span>
              </div>

              <div class="projects-page__item-actions">
                <button
                  data-testid="project-item-deps-button"
                  class="projects-page__action-btn"
                  title="Manage dependencies"
                  @click="openDepsModal(item)"
                >
                  <i class="fa-solid fa-link"></i>
                </button>
                <button
                  data-testid="project-item-edit-button"
                  class="projects-page__action-btn"
                  title="Edit item"
                  @click="openEditItem(item)"
                >
                  <i class="fa-solid fa-pen"></i>
                </button>
                <button
                  data-testid="project-item-archive-button"
                  class="projects-page__action-btn"
                  title="Archive item"
                  @click="handleArchiveItem(item.id)"
                >
                  <i class="fa-solid fa-box-archive"></i>
                </button>
                <button
                  data-testid="project-item-delete-button"
                  class="projects-page__action-btn projects-page__action-btn--danger"
                  title="Delete item"
                  @click="handleDeleteItem(item.id)"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>
          </template>
        </draggable>
      </template>
    </main>

    <!-- Modals -->
    <AddEditProjectModal
      :visible="showProjectModal"
      :edit-data="editProjectTarget"
      @close="closeProjectModal"
      @create="handleCreateProject"
      @update="handleUpdateProject"
    />

    <AddEditProjectItemModal
      :visible="showItemModal"
      :edit-data="editItemTarget"
      :project-id="store.selectedProjectId"
      @close="closeItemModal"
      @create="handleCreateItem"
      @update="handleUpdateItem"
    />

    <ManageDependenciesModal
      :visible="showDepsModal"
      :item-id="depsTargetId"
      :item-title="depsTargetTitle"
      :project-items="store.sortedItems"
      @close="closeDepsModal"
      @updated="onDepsUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import draggable from 'vuedraggable'
import { useProjectsStore } from '@/stores/projects'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type {
  ProjectWithItemCount,
  ProjectCreate,
  ProjectUpdate,
  ProjectItemInProject,
  ProjectItemCreate,
  ProjectItemUpdate,
  ProjectItem,
} from '@/api/client'
import AddEditProjectModal from '@/components/projects/AddEditProjectModal.vue'
import AddEditProjectItemModal from '@/components/projects/AddEditProjectItemModal.vue'
import ManageDependenciesModal from '@/components/projects/ManageDependenciesModal.vue'

const store = useProjectsStore()
const { show: notify } = useNotifications()

// --- Local arrays for vuedraggable (synced with store) ---
const localProjects = ref<ProjectWithItemCount[]>([])
const localItems = ref<ProjectItemInProject[]>([])

watch(
  () => store.sortedProjects,
  (val) => {
    localProjects.value = [...val]
  },
  { immediate: true }
)

watch(
  () => store.sortedItems,
  (val) => {
    localItems.value = [...val]
  },
  { immediate: true }
)

// --- Project modal state ---
const showProjectModal = ref(false)
const editProjectTarget = ref<{ id: number; name: string } | null>(null)

// --- Item modal state ---
const showItemModal = ref(false)
const editItemTarget = ref<{ id: number; title: string; notes?: string } | null>(null)

// --- Dependencies modal state ---
const showDepsModal = ref(false)
const depsTargetId = ref<number | null>(null)
const depsTargetTitle = ref('')

onMounted(() => {
  store.fetchProjects()
})

function selectProject(projectId: number) {
  store.fetchItems(projectId)
}

// --- Drag handlers ---

function onProjectDragEnd() {
  const orderedIds = localProjects.value.map((p) => p.id)
  store.reorderProjects(orderedIds).catch((e: unknown) => {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Reorder failed: ${detail}`, 'error')
  })
}

function onItemDragEnd() {
  const orderedIds = localItems.value.map((i) => i.id)
  store.reorderItems(orderedIds).catch((e: unknown) => {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Reorder failed: ${detail}`, 'error')
  })
}

// --- Blocker helpers ---

function isBlocked(itemId: number): boolean {
  const blockers = store.itemBlockers[itemId]
  return !!blockers && blockers.length > 0
}

function getBlockers(itemId: number): ProjectItem[] {
  return store.itemBlockers[itemId] ?? []
}

// --- Project handlers ---

function openEditProject(project: ProjectWithItemCount) {
  editProjectTarget.value = { id: project.id, name: project.name }
  showProjectModal.value = true
}

function closeProjectModal() {
  showProjectModal.value = false
  editProjectTarget.value = null
}

async function handleCreateProject(data: ProjectCreate) {
  try {
    await store.createProject(data)
    notify('Project added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add project: ${detail}`, 'error')
  }
}

async function handleUpdateProject(id: number, data: ProjectUpdate) {
  try {
    await store.updateProject(id, data)
    notify('Project updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update project: ${detail}`, 'error')
  }
}

async function handleDeleteProject(id: number) {
  try {
    await store.removeProject(id)
    notify('Project deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete project: ${detail}`, 'error')
  }
}

// --- Item handlers ---

function openEditItem(item: ProjectItemInProject) {
  editItemTarget.value = { id: item.id, title: item.title, notes: item.notes }
  showItemModal.value = true
}

function closeItemModal() {
  showItemModal.value = false
  editItemTarget.value = null
}

async function handleCreateItem(data: ProjectItemCreate) {
  try {
    await store.createItem(data)
    notify('Item added', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add item: ${detail}`, 'error')
  }
}

async function handleUpdateItem(id: number, data: ProjectItemUpdate) {
  try {
    await store.updateItem(id, data)
    notify('Item updated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update item: ${detail}`, 'error')
  }
}

async function handleToggleComplete(item: ProjectItemInProject) {
  try {
    await store.updateItem(item.id, { completed: !item.completed })
    notify(item.completed ? 'Item reopened' : 'Item completed', 'success')
    store.fetchItemBlockers()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update item: ${detail}`, 'error')
  }
}

async function handleArchiveItem(id: number) {
  try {
    await store.archiveItem(id)
    notify('Item archived', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to archive item: ${detail}`, 'error')
  }
}

async function handleDeleteItem(id: number) {
  try {
    await store.removeItem(id)
    notify('Item deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete item: ${detail}`, 'error')
  }
}

// --- Dependencies modal ---

function openDepsModal(item: ProjectItemInProject) {
  depsTargetId.value = item.id
  depsTargetTitle.value = item.title
  showDepsModal.value = true
}

function closeDepsModal() {
  showDepsModal.value = false
  depsTargetId.value = null
  depsTargetTitle.value = ''
}

function onDepsUpdated() {
  store.fetchItemBlockers()
}
</script>

<style scoped lang="scss">
.projects-page {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.5rem;
  min-height: calc(100vh - 6rem);

  &__sidebar {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  &__sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    h2 {
      margin: 0;
    }
  }

  &__empty {
    color: var(--clr-gray-500);
    font-style: italic;
  }

  &__project-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__project {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: var(--floating-box);
    transition: box-shadow 0.15s ease;

    &:hover {
      box-shadow: var(--bubble-box);
    }

    &--selected {
      box-shadow: var(--floating-box-pressed);
    }
  }

  &__drag-handle {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    cursor: grab;
    color: var(--clr-gray-500);
    font-size: 0.75rem;
    opacity: 0.4;
    transition: opacity 0.15s ease;

    .projects-page__project:hover &,
    .projects-page__item:hover & {
      opacity: 1;
    }

    &:active {
      cursor: grabbing;
    }
  }

  &__project-name {
    flex: 1;
    font-weight: 500;
  }

  &__project-count {
    color: var(--clr-gray-500);
    font-size: 0.85rem;
  }

  &__project-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.15s ease;

    .projects-page__project:hover & {
      opacity: 1;
    }
  }

  &__action-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    color: var(--clr-gray-500);
    font-size: 0.8rem;

    &:hover {
      color: var(--clr-text);
    }

    &--danger:hover {
      color: var(--clr-danger, #e74c3c);
    }
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  &__items-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    h2 {
      margin: 0;
    }
  }

  &__item-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    border-radius: 8px;
    box-shadow: var(--floating-box);

    &--completed {
      opacity: 0.6;

      .projects-page__item-title {
        text-decoration: line-through;
      }
    }

    &--archived {
      opacity: 0.4;
    }

    &--blocked {
      opacity: 0.5;

      .projects-page__item-title {
        color: var(--clr-gray-500);
      }
    }
  }

  &__check {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    font-size: 1.2rem;
    color: var(--clr-gray-500);
    flex-shrink: 0;
    margin-top: 0.1rem;

    &:hover {
      color: var(--clr-text);
    }
  }

  &__item-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
  }

  &__item-title {
    font-weight: 500;
  }

  &__item-notes {
    color: var(--clr-gray-500);
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__item-blockers {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--clr-danger, #e74c3c);
    font-size: 0.8rem;

    i {
      font-size: 0.7rem;
    }
  }

  &__item-actions {
    display: flex;
    gap: 0.25rem;
    flex-shrink: 0;
    opacity: 0;
    transition: opacity 0.15s ease;

    .projects-page__item:hover & {
      opacity: 1;
    }
  }

  // Drag ghost (the placeholder left behind)
  &__ghost {
    opacity: 0.3;
  }
}
</style>
