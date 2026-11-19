<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Activity,
  Archive,
  Check,
  CheckCheck,
  ChevronDown,
  LoaderCircle,
  LockKeyhole,
  Pin,
  Plus,
  RotateCcw,
  Search,
  Send,
  ShieldCheck,
  X,
} from 'lucide-vue-next'
import type { CatalogOption, OfferMutation, Stream } from '../types'
import { matchesOffer } from '../utils/campaigns'
import OfferPicker from './OfferPicker.vue'
import OfferTable from './OfferTable.vue'
import TrafficDistribution from './TrafficDistribution.vue'

const props = defineProps<{
  stream: Stream
  position: number
  disabled: boolean
  publishing: boolean
}>()
const emit = defineEmits<{
  mutate: [mutation: OfferMutation]
  cancel: []
  publish: []
}>()

const isAddingOffer = ref(false)
const isArchiveOpen = ref(false)
const offerQuery = ref('')
const selectedOffer = ref<CatalogOption | null>(null)
const activeOffers = computed(() => props.stream.offers.filter((offer) => !offer.removed))
const archivedOffers = computed(() => props.stream.offers.filter((offer) => offer.removed))
const visibleActiveOffers = computed(() =>
  activeOffers.value.filter((offer) => matchesOffer(offer, offerQuery.value)),
)
const visibleArchivedOffers = computed(() =>
  archivedOffers.value.filter((offer) => matchesOffer(offer, offerQuery.value)),
)
const pinnedCount = computed(() => activeOffers.value.filter((offer) => offer.pinned).length)
const excludedOfferIds = computed(() => props.stream.offers.map((offer) => offer.offer_id))
const controlsDisabled = computed(() => props.disabled || props.stream.source_missing)
const hasAllocationError = computed(
  () => activeOffers.value.length > 0 && props.stream.total_share !== 100,
)
const canPublish = computed(() => !controlsDisabled.value && !hasAllocationError.value)
const publicationHint = computed(() => {
  if (!activeOffers.value.length) return 'Все офферы будут убраны из потока в Keitaro.'
  if (props.stream.total_share !== 100)
    return 'Перед публикацией сумма долей должна составлять 100%.'
  return 'Изменения сохранятся в Keitaro после публикации.'
})

function addSelectedOffer(): void {
  if (selectedOffer.value) emit('mutate', { action: 'add', offer_id: selectedOffer.value.id })
}

watch(
  () => props.stream.revision,
  () => {
    selectedOffer.value = null
  },
)
watch(
  () => archivedOffers.value.length,
  (count, previousCount) => {
    if (count > previousCount) isArchiveOpen.value = true
  },
)

watch(offerQuery, (query) => {
  if (query.trim()) isArchiveOpen.value = true
})
</script>

<template>
  <article
    class="panel stream-card"
    :class="{ dirty: stream.dirty, 'source-missing': stream.source_missing }"
  >
    <div class="stream-header">
      <span
        class="flow-number"
        :class="{ 'flow-offers': stream.editable }"
      >
        {{ position }}
      </span>
      <div class="stream-title">
        <h3>{{ stream.name }}</h3>
        <small>
          #{{ stream.remote_id }} · {{ stream.editable ? 'Ротация офферов' : 'Технический поток' }}
        </small>
      </div>
      <span
        class="badge"
        :class="stream.source_missing ? 'danger' : stream.dirty ? 'amber' : 'neutral'"
      >
        <Activity
          v-if="stream.dirty"
          :size="14"
        />
        <Check
          v-else-if="!stream.source_missing"
          :size="14"
        />
        {{
          stream.source_missing ? 'Удалён в Keitaro' : stream.dirty ? 'Черновик' : 'Синхронизирован'
        }}
      </span>
    </div>

    <div
      v-if="stream.source_missing"
      class="stream-warning"
      role="status"
    >
      Поток отсутствует в Keitaro. Локальная история сохранена. Восстановите поток в трекере и
      синхронизируйте кампанию.
    </div>
    <div
      v-if="!stream.editable"
      class="non-offer-note"
    >
      <ShieldCheck :size="19" />
      <span>Фильтры и редирект этого потока настраиваются в Keitaro.</span>
      <LockKeyhole :size="15" />
    </div>

    <template v-else>
      <div class="distribution-section">
        <div class="distribution-heading">
          <span>Распределение трафика</span>
          <strong :class="{ 'error-text': hasAllocationError }">
            {{ activeOffers.length ? `${stream.total_share}%` : 'Нет офферов' }}
            <CheckCheck
              v-if="activeOffers.length && stream.total_share === 100"
              :size="16"
            />
          </strong>
        </div>
        <TrafficDistribution :offers="activeOffers" />
        <div class="distribution-caption">
          <span>Активных офферов: {{ activeOffers.length }}</span>
          <span v-if="pinnedCount">
            <Pin :size="13" />
            Закреплено: {{ pinnedCount }}
          </span>
        </div>
      </div>

      <div class="offer-toolbar">
        <div class="input-icon offer-search">
          <Search :size="16" />
          <input
            v-model="offerQuery"
            :aria-label="`Найти оффер в потоке ${stream.remote_id}`"
            placeholder="Поиск по названию или ID"
          />
          <button
            v-if="offerQuery"
            class="icon-button trailing"
            aria-label="Очистить поиск офферов"
            @click="offerQuery = ''"
          >
            <X :size="14" />
          </button>
        </div>
        <button
          class="button secondary add-offer-button"
          :disabled="controlsDisabled"
          :aria-expanded="isAddingOffer"
          @click="isAddingOffer = !isAddingOffer"
        >
          <Plus :size="16" />
          Добавить оффер
        </button>
      </div>
      <div
        v-if="isAddingOffer"
        class="add-offer-form"
      >
        <div>
          <label :for="`add-${stream.id}`">Выберите оффер из Keitaro</label>
          <OfferPicker
            :id="`add-${stream.id}`"
            v-model="selectedOffer"
            :exclude="excludedOfferIds"
            :disabled="controlsDisabled"
          />
        </div>
        <button
          class="button primary"
          :disabled="!selectedOffer || controlsDisabled"
          @click="addSelectedOffer"
        >
          Добавить
        </button>
        <button
          class="icon-button"
          aria-label="Закрыть добавление оффера"
          @click="isAddingOffer = false"
        >
          <X :size="18" />
        </button>
      </div>

      <OfferTable
        v-if="visibleActiveOffers.length"
        :offers="visibleActiveOffers"
        :disabled="controlsDisabled"
        @mutate="emit('mutate', $event)"
      />
      <div
        v-else
        class="offer-empty"
      >
        <strong>
          {{ offerQuery ? 'Активные офферы не найдены' : 'В потоке нет активных офферов' }}
        </strong>
        <span>
          {{
            offerQuery
              ? 'Измените запрос или проверьте архив ниже.'
              : 'Можно добавить новый оффер или вернуть его из архива.'
          }}
        </span>
      </div>

      <div
        v-if="archivedOffers.length"
        class="stream-archive"
      >
        <button
          class="archive-toggle"
          :aria-expanded="isArchiveOpen"
          :aria-controls="`archive-${stream.id}`"
          @click="isArchiveOpen = !isArchiveOpen"
        >
          <Archive :size="16" />
          <span>Архив</span>
          <span class="counter">{{ archivedOffers.length }}</span>
          <small>Можно вернуть в поток</small>
          <ChevronDown
            :size="16"
            :class="{ rotated: isArchiveOpen }"
          />
        </button>
        <div
          v-if="isArchiveOpen"
          :id="`archive-${stream.id}`"
        >
          <OfferTable
            v-if="visibleArchivedOffers.length"
            :offers="visibleArchivedOffers"
            :disabled="controlsDisabled"
            @mutate="emit('mutate', $event)"
          />
          <div
            v-else
            class="offer-empty"
          >
            В архиве нет офферов по этому запросу.
          </div>
        </div>
      </div>

      <div
        v-if="stream.dirty"
        class="draft-footer"
      >
        <div class="draft-footer-message">
          <strong>Изменения не опубликованы</strong>
          <span>{{ publicationHint }}</span>
        </div>
        <div class="draft-actions">
          <button
            class="button quiet"
            title="Cancel: отменить черновик"
            :disabled="controlsDisabled"
            @click="emit('cancel')"
          >
            <RotateCcw :size="16" />
            Отменить
          </button>
          <button
            class="button primary"
            title="Push to Keitaro"
            :disabled="!canPublish"
            @click="emit('publish')"
          >
            <LoaderCircle
              v-if="publishing"
              :size="16"
              class="spin"
            />
            <Send
              v-else
              :size="16"
            />
            {{ publishing ? 'Подождите…' : 'Опубликовать' }}
          </button>
        </div>
      </div>
    </template>
  </article>
</template>
