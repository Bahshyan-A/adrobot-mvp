<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ChevronDown, Globe2, Link2, LoaderCircle, Plus, SlidersHorizontal } from 'lucide-vue-next'
import OfferPicker from '../components/OfferPicker.vue'
import RoutingPreview from '../components/RoutingPreview.vue'
import type { Catalog, CatalogOption, CreateCampaignRequest } from '../types'
import { catalogName } from '../utils/format'
const props = defineProps<{ catalog: Catalog; isBusy: boolean; campaignNamePrefix: string }>()
const emit = defineEmits<{
  create: [body: CreateCampaignRequest]
  error: [message: string]
  cancel: []
}>()
const form = reactive({
  nameSuffix: '',
  geo: 'AU',
  domain_id: props.catalog.domains[0]?.id ?? 0,
  group_id: preferredOption(props.catalog.groups),
  traffic_source_id: preferredOption(props.catalog.traffic_sources),
  offer: null as CatalogOption | null,
})
const geoCodes = computed(() =>
  form.geo
    .toUpperCase()
    .split(/[\s,;]+/)
    .filter(Boolean),
)
const domainName = computed(() => catalogName(props.catalog, 'domains', form.domain_id))
const campaignName = computed(() => {
  const enteredName = form.nameSuffix.trim()
  return enteredName.startsWith(props.campaignNamePrefix)
    ? enteredName
    : props.campaignNamePrefix + enteredName
})
function preferredOption(options: CatalogOption[]): number {
  return (options.find((option) => option.name === 'FORTESTS') ?? options[0])?.id ?? 0
}
function submit(): void {
  if (!form.offer) {
    emit('error', 'Выберите оффер из результатов поиска.')
    return
  }
  emit('create', {
    name: campaignName.value,
    geo: geoCodes.value,
    offer_id: form.offer.id,
    domain_id: form.domain_id,
    group_id: form.group_id,
    traffic_source_id: form.traffic_source_id,
  })
}
</script>

<template>
  <div class="creation-layout">
    <form
      class="panel creation-form"
      @submit.prevent="submit"
    >
      <div class="panel-heading">
        <span class="section-icon"><SlidersHorizontal :size="19" /></span>
        <div>
          <h2>Параметры кампании</h2>
          <p>Название, правила гео и первый оффер</p>
        </div>
      </div>
      <div class="form-section">
        <label for="campaign-name">
          Название кампании
          <span class="required">*</span>
        </label>
        <div class="campaign-name-input">
          <span class="campaign-name-prefix">{{ campaignNamePrefix }}</span>
          <input
            id="campaign-name"
            v-model="form.nameSuffix"
            required
            :maxlength="255 - campaignNamePrefix.length"
            placeholder="campaign1"
            :disabled="isBusy"
            aria-describedby="campaign-name-hint"
          />
        </div>
        <p
          id="campaign-name-hint"
          class="field-hint"
        >
          Префикс тестового задания добавляется автоматически.
        </p>
        <div class="field">
          <label for="campaign-geo">
            Гео для первого потока
            <span class="required">*</span>
          </label>
          <div class="input-icon">
            <Globe2 :size="18" />
            <input
              id="campaign-geo"
              v-model="form.geo"
              required
              placeholder="AU, MX, RO"
              :disabled="isBusy"
            />
          </div>
          <p class="field-hint">ISO-коды стран через запятую. Этот трафик уйдёт на google.com.</p>
        </div>
        <div class="field">
          <label for="initial-offer">
            Оффер
            <span class="required">*</span>
          </label>
          <OfferPicker
            id="initial-offer"
            v-model="form.offer"
            :disabled="isBusy"
          />
          <p class="field-hint">Для всех посетителей из остальных стран.</p>
        </div>
      </div>
      <div class="form-section integration-section">
        <div class="subsection-heading">
          <Link2 :size="17" />
          <h3>Настройки Keitaro</h3>
        </div>
        <label for="domain">
          Домен
          <span class="required">*</span>
        </label>
        <div class="select-wrap">
          <select
            id="domain"
            v-model="form.domain_id"
            required
            :disabled="isBusy"
          >
            <option
              v-for="item in catalog.domains"
              :key="item.id"
              :value="item.id"
            >
              {{ item.name }}
            </option>
            <option
              v-if="!catalog.domains.length"
              :value="0"
              disabled
            >
              Нет доступных доменов
            </option>
          </select>
          <ChevronDown :size="16" />
        </div>
        <div class="form-two-col field">
          <div>
            <label for="group">
              Группа
              <span class="required">*</span>
            </label>
            <div class="select-wrap">
              <select
                id="group"
                v-model="form.group_id"
                :disabled="isBusy"
              >
                <option
                  v-for="item in catalog.groups"
                  :key="item.id"
                  :value="item.id"
                >
                  {{ item.name }}
                </option>
              </select>
              <ChevronDown :size="16" />
            </div>
          </div>
          <div>
            <label for="source">
              Источник
              <span class="required">*</span>
            </label>
            <div class="select-wrap">
              <select
                id="source"
                v-model="form.traffic_source_id"
                :disabled="isBusy"
              >
                <option
                  v-for="item in catalog.traffic_sources"
                  :key="item.id"
                  :value="item.id"
                >
                  {{ item.name }}
                </option>
              </select>
              <ChevronDown :size="16" />
            </div>
          </div>
        </div>
      </div>
      <div class="form-footer">
        <button
          type="button"
          class="button secondary"
          :disabled="isBusy"
          @click="emit('cancel')"
        >
          К кампаниям
        </button>
        <button
          class="button primary"
          :disabled="isBusy || !form.domain_id || !form.group_id || !form.traffic_source_id"
        >
          <LoaderCircle
            v-if="isBusy"
            :size="17"
            class="spin"
          />
          <Plus
            v-else
            :size="17"
          />
          {{ isBusy ? 'Создаём…' : 'Создать кампанию' }}
        </button>
      </div>
    </form>
    <RoutingPreview
      :name="campaignName"
      :geo-codes="geoCodes"
      :domain-name="domainName"
      :offer="form.offer"
    />
  </div>
</template>
