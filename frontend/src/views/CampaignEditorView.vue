<script setup lang="ts">
import { computed } from 'vue'
import { CheckCheck, History, Layers, Pin, Plus, RefreshCw, Workflow } from 'lucide-vue-next'
import CampaignBrowser from '../components/CampaignBrowser.vue'
import CampaignOverview from '../components/CampaignOverview.vue'
import StreamCard from '../components/StreamCard.vue'
import type { Campaign, CampaignSummary, Catalog, OfferMutation, Stream } from '../types'
import { formatTime } from '../utils/format'

const props = defineProps<{
  campaigns: CampaignSummary[]
  selectedCampaign: Campaign | null
  campaignNamePrefix: string
  catalog: Catalog
  isBusy: boolean
  pendingStreamId: number | null
  syncChanges: string[]
}>()
const emit = defineEmits<{
  create: []
  refresh: []
  select: [id: number]
  fetch: []
  history: []
  dismissChanges: []
  editOffer: [stream: Stream, mutation: OfferMutation]
  cancel: [stream: Stream]
  publish: [stream: Stream]
}>()

const dirtyCount = computed(
  () => props.selectedCampaign?.streams.filter((stream) => stream.dirty).length ?? 0,
)
const activeOfferCount = computed(
  () =>
    props.selectedCampaign?.streams.reduce((count, stream) => count + stream.active_count, 0) ?? 0,
)
const controlsDisabled = computed(() => props.isBusy || props.pendingStreamId !== null)
</script>

<template>
  <div
    v-if="!campaigns.length"
    class="panel empty-state"
  >
    <span class="empty-state-icon"><Layers :size="28" /></span>
    <h2>Создайте первую кампанию</h2>
    <p>Выберите гео и оффер. Два потока и маршрутизацию мы настроим автоматически.</p>
    <button
      class="button primary"
      @click="emit('create')"
    >
      <Plus :size="18" />
      Создать кампанию
    </button>
    <button
      class="text-button"
      :disabled="controlsDisabled"
      @click="emit('refresh')"
    >
      Обновить список
    </button>
  </div>

  <div
    v-else
    class="editor-layout"
  >
    <CampaignBrowser
      :campaigns="campaigns"
      :selected-id="selectedCampaign?.id"
      :name-prefix="campaignNamePrefix"
      :disabled="controlsDisabled"
      @select="emit('select', $event)"
      @create="emit('create')"
    />

    <section
      v-if="selectedCampaign"
      class="campaign-editor"
      :aria-busy="isBusy"
    >
      <div class="editor-context">
        <span>Рабочая область кампании</span>
        <button
          class="text-button muted-button"
          :disabled="controlsDisabled"
          @click="emit('refresh')"
        >
          <RefreshCw
            :size="15"
            :class="{ spin: isBusy }"
          />
          Обновить список
        </button>
      </div>
      <CampaignOverview
        :campaign="selectedCampaign"
        :catalog="catalog"
      />

      <div class="streams-heading">
        <div>
          <h2>
            Потоки и офферы
            <span class="counter">{{ selectedCampaign.streams.length }}</span>
          </h2>
          <p>
            Активных офферов: {{ activeOfferCount }}. Снимок от
            {{ formatTime(selectedCampaign.synced_at) }}.
          </p>
        </div>
        <div class="stream-toolbar">
          <button
            class="button secondary history-button"
            :disabled="controlsDisabled"
            @click="emit('history')"
          >
            <History :size="16" />
            <span>История</span>
          </button>
          <button
            class="button secondary"
            :disabled="controlsDisabled"
            title="Fetch streams: сверить с Keitaro"
            @click="emit('fetch')"
          >
            <RefreshCw
              :size="16"
              :class="{ spin: isBusy }"
            />
            Синхронизировать
          </button>
        </div>
      </div>

      <div
        v-if="dirtyCount"
        class="draft-notice"
        role="status"
      >
        <span class="draft-notice-icon"><Pin :size="18" /></span>
        <div>
          <strong>Есть неопубликованные изменения</strong>
          <p>
            Потоков с черновиком: {{ dirtyCount }}. Проверьте доли и нажмите «Опубликовать» в нужном
            потоке.
          </p>
        </div>
      </div>
      <div
        v-else
        class="synced-note"
      >
        <CheckCheck :size="16" />
        Локальных изменений нет
      </div>

      <div
        v-if="syncChanges.length"
        class="sync-changes"
      >
        <strong>Изменения в Keitaro</strong>
        <ul>
          <li
            v-for="change in syncChanges"
            :key="change"
          >
            {{ change }}
          </li>
        </ul>
        <button
          class="text-button"
          @click="emit('dismissChanges')"
        >
          Скрыть
        </button>
      </div>
      <div
        v-if="!selectedCampaign.streams.length"
        class="panel empty-state"
      >
        <Workflow :size="30" />
        <h2>В кампании нет потоков</h2>
        <p>Создайте поток в Keitaro и нажмите «Синхронизировать».</p>
      </div>

      <StreamCard
        v-for="(stream, index) in selectedCampaign.streams"
        :key="stream.id"
        :stream="stream"
        :position="index + 1"
        :disabled="controlsDisabled"
        :publishing="pendingStreamId === stream.id"
        @mutate="emit('editOffer', stream, $event)"
        @cancel="emit('cancel', stream)"
        @publish="emit('publish', stream)"
      />
      <div class="editor-footnote">
        <Pin :size="14" />
        Булавка фиксирует долю. Остаток распределяется между остальными офферами.
      </div>
    </section>
  </div>
</template>
