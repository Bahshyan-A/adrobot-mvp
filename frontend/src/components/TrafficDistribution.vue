<script setup lang="ts">
import { computed } from 'vue'
import type { Offer } from '../types'

const props = defineProps<{ offers: Offer[] }>()
const description = computed(() =>
  props.offers.map((offer) => `${offer.name}: ${offer.share}%`).join(', '),
)
</script>

<template>
  <div
    class="traffic-distribution"
    role="img"
    :aria-label="`Распределение трафика. ${description || 'Нет активных офферов'}`"
  >
    <span
      v-for="(offer, index) in offers"
      :key="offer.offer_id"
      class="traffic-segment"
      :class="`traffic-shade-${index % 4}`"
      :style="{ width: `${offer.share}%` }"
      :title="`${offer.name} — ${offer.share}%`"
      aria-hidden="true"
    ></span>
  </div>
</template>
