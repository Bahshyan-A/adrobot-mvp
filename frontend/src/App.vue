<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, LoaderCircle, LockKeyhole, Plus, ShieldCheck, Unplug, X } from 'lucide-vue-next'
import WorkspaceDialogs from './components/WorkspaceDialogs.vue'
import WorkspaceHeader from './components/WorkspaceHeader.vue'
import WorkspaceSidebar from './components/WorkspaceSidebar.vue'
import { useCampaignWorkspace } from './composables/useCampaignWorkspace'
import type { WorkspacePage } from './types'
import CampaignCreateView from './views/CampaignCreateView.vue'
import CampaignEditorView from './views/CampaignEditorView.vue'

const {
  page,
  campaignNamePrefix,
  catalog,
  campaigns,
  selectedCampaign,
  isLoading,
  isBusy,
  pendingStreamId,
  needsAuthentication,
  error,
  notification,
  syncChanges,
  syncConflict,
  pendingCancel,
  history,
  navigate,
  loadWorkspace,
  login,
  selectCampaign,
  createCampaign,
  fetchStreams,
  editOffer,
  publishStream,
  confirmCancel,
  loadHistory,
} = useCampaignWorkspace()

const isHelpOpen = ref(false)
const isMobileMenuOpen = ref(false)
const applicationToken = ref('')
const heading = computed(() => (page.value === 'create' ? 'Новая кампания' : 'Кампании'))
const description = computed(() =>
  page.value === 'create'
    ? 'Одна форма. Два потока. Всё готово к запуску.'
    : 'Настраивайте потоки и управляйте распределением трафика.',
)

function changePage(nextPage: WorkspacePage): void {
  navigate(nextPage)
  isMobileMenuOpen.value = false
}
</script>

<template>
  <div
    class="workspace"
    @keydown.esc="isMobileMenuOpen = false"
  >
    <button
      v-if="isMobileMenuOpen"
      class="navigation-backdrop"
      aria-label="Закрыть навигацию"
      @click="isMobileMenuOpen = false"
    ></button>
    <WorkspaceSidebar
      :page="page"
      :campaign-count="campaigns.length"
      :open="isMobileMenuOpen"
      @navigate="changePage"
      @help="isHelpOpen = true"
      @close="isMobileMenuOpen = false"
    />
    <div class="main-area">
      <WorkspaceHeader
        :page="page"
        :menu-open="isMobileMenuOpen"
        @toggle-menu="isMobileMenuOpen = !isMobileMenuOpen"
        @help="isHelpOpen = true"
      />
      <main>
        <form
          v-if="needsAuthentication"
          class="auth-panel panel"
          @submit.prevent="login(applicationToken)"
        >
          <LockKeyhole :size="28" />
          <h1>Вход в рабочее пространство</h1>
          <label for="app-token">Токен приложения</label>
          <input
            id="app-token"
            v-model="applicationToken"
            type="password"
            required
            autocomplete="current-password"
          />
          <button
            class="button primary"
            :disabled="isLoading"
          >
            Войти
          </button>
          <p
            v-if="error"
            class="error-text"
            role="alert"
          >
            {{ error }}
          </p>
        </form>

        <template v-else>
          <div class="page-heading">
            <div>
              <h1>{{ heading }}</h1>
              <p>{{ description }}</p>
            </div>
            <button
              v-if="page === 'campaigns'"
              class="button primary"
              @click="changePage('create')"
            >
              <Plus :size="18" />
              Новая кампания
            </button>
            <span
              v-else
              class="heading-note"
            >
              <ShieldCheck :size="17" />
              Настройки сохраняются в Keitaro
            </span>
          </div>

          <div
            v-if="error"
            class="error-banner"
            role="alert"
          >
            <Unplug :size="19" />
            <span>{{ error }}</span>
            <button
              class="icon-button"
              aria-label="Закрыть сообщение об ошибке"
              @click="error = ''"
            >
              <X :size="17" />
            </button>
          </div>

          <div
            v-if="isLoading"
            class="loading-state"
          >
            <LoaderCircle
              :size="26"
              class="spin"
            />
            <p>Загружаем рабочее пространство…</p>
          </div>
          <KeepAlive v-else>
            <CampaignCreateView
              v-if="page === 'create'"
              :catalog="catalog"
              :campaign-name-prefix="campaignNamePrefix"
              :is-busy="isBusy"
              @create="createCampaign"
              @error="error = $event"
              @cancel="changePage('campaigns')"
            />
            <CampaignEditorView
              v-else
              :campaigns="campaigns"
              :campaign-name-prefix="campaignNamePrefix"
              :selected-campaign="selectedCampaign"
              :catalog="catalog"
              :is-busy="isBusy"
              :pending-stream-id="pendingStreamId"
              :sync-changes="syncChanges"
              @create="changePage('create')"
              @refresh="loadWorkspace"
              @select="selectCampaign"
              @fetch="fetchStreams()"
              @history="loadHistory"
              @dismiss-changes="syncChanges = []"
              @edit-offer="editOffer"
              @cancel="pendingCancel = $event"
              @publish="publishStream"
            />
          </KeepAlive>
          <footer class="page-footer">
            <span>Adrobot · Campaign workspace</span>
            <span>
              <ShieldCheck :size="13" />
              Работает с Keitaro Admin API
            </span>
          </footer>
        </template>
      </main>
    </div>

    <Transition name="toast">
      <div
        v-if="notification"
        role="status"
        class="toast-message"
      >
        <span><Check :size="16" /></span>
        {{ notification }}
      </div>
    </Transition>
    <WorkspaceDialogs
      :campaign-name-prefix="campaignNamePrefix"
      :help-open="isHelpOpen"
      :pending-cancel="pendingCancel"
      :conflict="syncConflict"
      :history="history"
      :disabled="isBusy || pendingStreamId !== null"
      :error="error"
      @close-help="isHelpOpen = false"
      @close-cancel="pendingCancel = null"
      @close-conflict="syncConflict = null"
      @close-history="history = null"
      @confirm-cancel="confirmCancel"
      @discard-and-fetch="fetchStreams(true)"
    />
  </div>
</template>
