<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronRight, Layers, Plus, Search, X } from 'lucide-vue-next'
import type { CampaignSummary } from '../types'
import { matchesCampaign, type CampaignScope } from '../utils/campaigns'

const props = defineProps<{
  campaigns: CampaignSummary[]
  selectedId?: number
  namePrefix: string
  disabled: boolean
}>()
const emit = defineEmits<{ select: [id: number]; create: [] }>()
const query = ref('')
const scope = ref<CampaignScope>('all')
const scopes: { value: CampaignScope; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'own', label: 'Мои' },
  { value: 'drafts', label: 'Черновики' },
]
const filteredCampaigns = computed(() =>
  props.campaigns.filter((campaign) =>
    matchesCampaign(campaign, query.value, scope.value, props.namePrefix),
  ),
)

function resetFilters(): void {
  query.value = ''
  scope.value = 'all'
}
</script>

<template>
  <aside
    class="campaign-list panel"
    aria-label="Выбор кампании"
  >
    <div class="list-heading">
      <h2>Кампании</h2>
      <span class="counter">{{ campaigns.length }}</span>
    </div>
    <div class="campaign-browser-controls">
      <div class="input-icon campaign-search">
        <Search :size="17" />
        <input
          v-model="query"
          aria-label="Найти кампанию"
          placeholder="Название или ID"
        />
        <button
          v-if="query"
          class="icon-button trailing"
          aria-label="Очистить поиск кампаний"
          @click="query = ''"
        >
          <X :size="15" />
        </button>
      </div>
      <div
        class="scope-filters"
        role="group"
        aria-label="Фильтр кампаний"
      >
        <button
          v-for="filter in scopes"
          :key="filter.value"
          :aria-pressed="scope === filter.value"
          :class="{ active: scope === filter.value }"
          :title="filter.value === 'own' ? `Кампании с префиксом ${namePrefix}` : undefined"
          @click="scope = filter.value"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>

    <div class="campaign-list-items">
      <button
        v-for="campaign in filteredCampaigns"
        :key="campaign.id"
        class="campaign-item"
        :class="{ selected: selectedId === campaign.id }"
        :aria-current="selectedId === campaign.id ? 'true' : undefined"
        :disabled="disabled"
        @click="emit('select', campaign.id)"
      >
        <span class="campaign-item-icon"><Layers :size="18" /></span>
        <span class="campaign-item-content">
          <strong :title="campaign.name">{{ campaign.name }}</strong>
          <small>
            #{{ campaign.id }}
            <span
              class="campaign-state"
              :class="{ inactive: campaign.state !== 'active' }"
            >
              {{ campaign.state === 'active' ? 'Активна' : 'Отключена' }}
            </span>
          </small>
          <span
            v-if="campaign.dirty_count"
            class="campaign-draft-label"
          >
            Есть черновик
          </span>
        </span>
        <ChevronRight :size="15" />
      </button>
      <div
        v-if="!filteredCampaigns.length"
        class="browser-empty"
      >
        <Search :size="22" />
        <strong>Кампании не найдены</strong>
        <p>Измените запрос или выбранный фильтр.</p>
        <button
          class="text-button"
          @click="resetFilters"
        >
          Сбросить фильтры
        </button>
      </div>
    </div>

    <div class="campaign-list-footer">
      <span>Показано {{ filteredCampaigns.length }} из {{ campaigns.length }}</span>
      <button
        class="icon-button"
        title="Создать кампанию"
        aria-label="Создать кампанию"
        @click="emit('create')"
      >
        <Plus :size="18" />
      </button>
    </div>
  </aside>
</template>
