<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Check, Copy, Globe2, Layers, Link2, Radio } from 'lucide-vue-next'
import type { Campaign, Catalog } from '../types'
import { catalogName } from '../utils/format'

const props = defineProps<{ campaign: Campaign; catalog: Catalog }>()
const copyStatus = ref<'idle' | 'copied' | 'failed'>('idle')
let resetTimer: ReturnType<typeof setTimeout> | undefined
const campaignUrl = computed(() => {
  const domain = catalogName(props.catalog, 'domains', props.campaign.domain_id)
  if (domain === '—') return ''
  const base = /^https?:\/\//i.test(domain) ? domain : `https://${domain}`
  return `${base.replace(/\/$/, '')}/${props.campaign.alias}`
})

async function copyUrl(): Promise<void> {
  try {
    await navigator.clipboard.writeText(campaignUrl.value)
    copyStatus.value = 'copied'
  } catch {
    copyStatus.value = 'failed'
  }
  clearTimeout(resetTimer)
  resetTimer = setTimeout(() => (copyStatus.value = 'idle'), 4000)
}

function selectLink(event: FocusEvent): void {
  const input = event.target as HTMLInputElement
  input.select()
}

watch(
  () => props.campaign.id,
  () => {
    copyStatus.value = 'idle'
  },
)
onBeforeUnmount(() => clearTimeout(resetTimer))
</script>

<template>
  <div class="panel campaign-overview">
    <div class="campaign-title-row">
      <div>
        <div class="campaign-id">Кампания #{{ campaign.id }}</div>
        <h2>{{ campaign.name }}</h2>
      </div>
      <span
        class="badge"
        :class="campaign.state === 'active' ? 'green' : 'neutral'"
      >
        {{ campaign.state === 'active' ? 'Активна' : 'Отключена' }}
      </span>
    </div>
    <dl class="campaign-meta">
      <div>
        <dt>
          <Globe2 :size="15" />
          Домен
        </dt>
        <dd :title="catalogName(catalog, 'domains', campaign.domain_id)">
          {{ catalogName(catalog, 'domains', campaign.domain_id).replace(/^https?:\/\//, '') }}
        </dd>
      </div>
      <div>
        <dt>
          <Layers :size="15" />
          Группа
        </dt>
        <dd>{{ catalogName(catalog, 'groups', campaign.group_id) }}</dd>
      </div>
      <div>
        <dt>
          <Radio :size="15" />
          Источник
        </dt>
        <dd>{{ catalogName(catalog, 'traffic_sources', campaign.traffic_source_id) }}</dd>
      </div>
    </dl>
    <div class="campaign-link">
      <Link2 :size="17" />
      <label
        class="sr-only"
        :for="`campaign-link-${campaign.id}`"
      >
        Ссылка кампании
      </label>
      <input
        :id="`campaign-link-${campaign.id}`"
        :value="campaignUrl"
        readonly
        placeholder="Домен не указан"
        @focus="selectLink"
      />
      <button
        class="button secondary copy-button"
        :disabled="!campaignUrl"
        aria-label="Скопировать ссылку кампании"
        @click="copyUrl"
      >
        <Check
          v-if="copyStatus === 'copied'"
          :size="16"
        />
        <Copy
          v-else
          :size="16"
        />
        <span>{{ copyStatus === 'copied' ? 'Скопировано' : 'Копировать' }}</span>
      </button>
    </div>
    <p
      v-if="copyStatus === 'failed'"
      class="copy-feedback"
      role="status"
    >
      Выделите ссылку и скопируйте её вручную.
    </p>
    <span
      v-if="copyStatus === 'copied'"
      class="sr-only"
      role="status"
    >
      Ссылка скопирована
    </span>
  </div>
</template>
