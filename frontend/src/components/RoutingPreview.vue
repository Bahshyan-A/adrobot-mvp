<script setup lang="ts">
import { Globe2, Layers, Link2, ShieldCheck } from 'lucide-vue-next'
import type { CatalogOption } from '../types'
defineProps<{ name: string; geoCodes: string[]; domainName: string; offer: CatalogOption | null }>()
</script>

<template>
  <aside class="preview-column">
    <div class="panel routing-preview">
      <div class="preview-heading">
        <h2>Маршрут трафика</h2>
        <span class="badge neutral">Предпросмотр</span>
      </div>
      <p class="preview-description">Как будут распределяться посетители</p>
      <div class="route-entry">
        <span class="route-icon"><Link2 :size="20" /></span>
        <div>
          <strong>{{ name || 'Ваша кампания' }}</strong>
          <small>{{ domainName }}</small>
        </div>
      </div>
      <div class="route-line"><span>Проверяем страну посетителя</span></div>
      <div class="route-card">
        <div class="route-card-heading">
          <span class="flow-number">1</span>
          <strong>Геофильтр</strong>
          <span class="badge accent">Приоритетный</span>
        </div>
        <div class="geo-tags">
          <span
            v-for="code in geoCodes"
            :key="code"
          >
            <Globe2 :size="13" />
            {{ code }}
          </span>
          <span v-if="!geoCodes.length">Выберите гео</span>
        </div>
        <div class="route-destination">
          <span class="route-icon"><Globe2 :size="18" /></span>
          <div>
            <strong>google.com</strong>
            <small>Прямой редирект</small>
          </div>
        </div>
      </div>
      <div class="route-line secondary-line"><span>Все остальные страны</span></div>
      <div class="route-card">
        <div class="route-card-heading">
          <span class="flow-number flow-offers">2</span>
          <strong>Основной поток</strong>
        </div>
        <div class="route-destination">
          <span class="offer-symbol"><Layers :size="19" /></span>
          <div>
            <strong>{{ offer?.name || 'Выбранный оффер' }}</strong>
            <small>{{ offer ? '#' + offer.id : 'Выберите оффер в форме' }}</small>
          </div>
          <span class="route-percent">
            100
            <span>%</span>
          </span>
        </div>
      </div>
    </div>
    <div class="info-note">
      <ShieldCheck :size="20" />
      <div>
        <strong>Готова после создания</strong>
        <p>Домен, группа, источник и оба потока настроятся автоматически.</p>
      </div>
    </div>
  </aside>
</template>
