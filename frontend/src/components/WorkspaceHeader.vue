<script setup lang="ts">
import { ChevronRight, CircleHelp, Menu } from 'lucide-vue-next'
import type { WorkspacePage } from '../types'
defineProps<{ page: WorkspacePage; menuOpen: boolean }>()
const emit = defineEmits<{ toggleMenu: []; help: [] }>()
</script>

<template>
  <header class="topbar">
    <div class="breadcrumb">
      <button
        class="icon-button mobile-menu"
        aria-label="Открыть меню"
        :aria-expanded="menuOpen"
        aria-controls="workspace-navigation"
        @click="emit('toggleMenu')"
      >
        <Menu :size="20" />
      </button>
      <span>Adrobot</span>
      <ChevronRight :size="14" />
      <strong>{{ page === 'create' ? 'Новая кампания' : 'Кампании' }}</strong>
    </div>
    <div class="topbar-right">
      <span class="environment">
        <span class="status-dot"></span>
        Keitaro
      </span>
      <button
        class="button help-button"
        aria-label="Справка"
        @click="emit('help')"
      >
        <CircleHelp :size="20" />
        Справка
      </button>
    </div>
  </header>
</template>
