<script setup lang="ts">
import { CircleHelp, Layers, Plus, ShieldCheck, Workflow, X } from 'lucide-vue-next'
import type { WorkspacePage } from '../types'
defineProps<{ page: WorkspacePage; campaignCount: number; open: boolean }>()
const emit = defineEmits<{ navigate: [page: WorkspacePage]; help: []; close: [] }>()
</script>

<template>
  <aside
    class="sidebar"
    :class="{ 'mobile-open': open }"
  >
    <button
      class="icon-button sidebar-close"
      aria-label="Закрыть меню"
      @click="emit('close')"
    >
      <X :size="20" />
    </button>
    <a
      class="brand"
      href="#campaigns"
      aria-label="Adrobot — кампании"
      @click="emit('navigate', 'campaigns')"
    >
      <span class="brand-symbol">
        <Workflow
          :size="23"
          :stroke-width="2.4"
        />
      </span>
      adrobot
      <span class="brand-period">.</span>
    </a>
    <div class="workspace-switch">
      <span class="workspace-avatar">A</span>
      <span>
        <strong>Кампании Keitaro</strong>
        <small>Управление трафиком</small>
      </span>
    </div>
    <div class="nav-label">Рабочая область</div>
    <nav
      id="workspace-navigation"
      aria-label="Основная навигация"
    >
      <a
        href="#campaigns"
        :class="{ active: page === 'campaigns' }"
        :aria-current="page === 'campaigns' ? 'page' : undefined"
        @click="emit('navigate', 'campaigns')"
      >
        <Layers :size="19" />
        Кампании
        <span class="nav-count">{{ campaignCount }}</span>
      </a>
      <a
        href="#create"
        :class="{ active: page === 'create' }"
        :aria-current="page === 'create' ? 'page' : undefined"
        @click="emit('navigate', 'create')"
      >
        <Plus :size="19" />
        Создать кампанию
      </a>
    </nav>
    <div class="sidebar-guide">
      <div class="guide-icon"><ShieldCheck :size="22" /></div>
      <strong>Черновики под контролем</strong>
      <p>Изменения офферов попадут в Keitaro после нажатия «Опубликовать».</p>
      <button
        class="text-button"
        @click="emit('help')"
      >
        <CircleHelp :size="15" />
        Как это работает
      </button>
    </div>
    <div class="sidebar-bottom">
      <div class="connection">
        <span class="status-dot"></span>
        <span>Keitaro Admin API</span>
        <ShieldCheck :size="16" />
      </div>
      <div class="version">
        Adrobot
        <span>v1.0</span>
      </div>
    </div>
  </aside>
</template>
