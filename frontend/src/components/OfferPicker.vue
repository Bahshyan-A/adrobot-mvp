<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Check, LoaderCircle, Search, X } from 'lucide-vue-next'
import { campaignApi } from '../api'
import type { CatalogOption } from '../types'
import { errorMessage } from '../utils/format'

const props = withDefaults(
  defineProps<{
    modelValue: CatalogOption | null
    id: string
    exclude?: number[]
    disabled?: boolean
  }>(),
  { exclude: () => [] },
)
const emit = defineEmits<{ 'update:modelValue': [offer: CatalogOption | null] }>()

const query = ref(props.modelValue?.name ?? '')
const results = ref<CatalogOption[]>([])
const isOpen = ref(false)
const isLoading = ref(false)
const error = ref('')
const highlightedIndex = ref(0)
const availableOffers = computed(() =>
  results.value.filter((offer) => !props.exclude.includes(offer.id)),
)
let debounceTimer: ReturnType<typeof setTimeout> | undefined
let controller: AbortController | undefined

watch(
  () => props.modelValue,
  (offer) => {
    if (offer) query.value = offer.name
    else if (!isOpen.value) query.value = ''
  },
)

async function search(): Promise<void> {
  controller?.abort()
  const activeController = new AbortController()
  controller = activeController
  isLoading.value = true
  error.value = ''

  try {
    const offers = await campaignApi.searchOffers(query.value, activeController.signal)
    if (!activeController.signal.aborted) {
      results.value = offers
      highlightedIndex.value = 0
    }
  } catch (cause) {
    if (!activeController.signal.aborted) error.value = errorMessage(cause)
  } finally {
    if (controller === activeController) isLoading.value = false
  }
}

function handleInput(): void {
  controller?.abort()
  results.value = []
  isLoading.value = true
  emit('update:modelValue', null)
  isOpen.value = true
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => void search(), 250)
}

function selectOffer(offer: CatalogOption): void {
  query.value = offer.name
  isOpen.value = false
  emit('update:modelValue', offer)
}

function clearSelection(): void {
  query.value = ''
  isOpen.value = false
  emit('update:modelValue', null)
}

function handleFocus(): void {
  isOpen.value = true
  if (!props.modelValue) void search()
}

function handleFocusOut(event: FocusEvent): void {
  const container = event.currentTarget as HTMLElement
  if (!container.contains(event.relatedTarget as Node | null)) isOpen.value = false
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') isOpen.value = false
  if (isLoading.value) return

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    isOpen.value = true
    const direction = event.key === 'ArrowDown' ? 1 : -1
    highlightedIndex.value = Math.max(
      0,
      Math.min(availableOffers.value.length - 1, highlightedIndex.value + direction),
    )
  }

  const highlightedOffer = availableOffers.value[highlightedIndex.value]
  if (event.key === 'Enter' && isOpen.value && highlightedOffer) {
    event.preventDefault()
    selectOffer(highlightedOffer)
  }
}

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
  controller?.abort()
})
</script>

<template>
  <div
    class="offer-picker"
    @focusout="handleFocusOut"
  >
    <div class="input-icon">
      <Search :size="17" />
      <input
        :id="id"
        v-model="query"
        role="combobox"
        aria-autocomplete="list"
        autocomplete="off"
        :aria-expanded="isOpen"
        :aria-controls="`${id}-results`"
        :aria-activedescendant="
          isOpen && availableOffers.length ? `${id}-option-${highlightedIndex}` : undefined
        "
        :disabled="disabled"
        placeholder="Название или ID оффера"
        @input="handleInput"
        @focus="handleFocus"
        @keydown="handleKeydown"
      />
      <LoaderCircle
        v-if="isLoading"
        :size="17"
        class="spin trailing"
      />
      <button
        v-else-if="modelValue"
        type="button"
        class="icon-button trailing"
        aria-label="Очистить выбранный оффер"
        @click="clearSelection"
      >
        <X :size="15" />
      </button>
    </div>

    <div
      v-if="isOpen"
      :id="`${id}-results`"
      class="picker-results"
      role="listbox"
    >
      <div
        v-if="error"
        class="picker-empty error-text"
      >
        {{ error }}
      </div>
      <div
        v-else-if="isLoading"
        class="picker-empty"
      >
        Поиск офферов…
      </div>
      <div
        v-else-if="!availableOffers.length"
        class="picker-empty"
      >
        Офферы не найдены. Измените название или ID.
      </div>
      <template v-else>
        <button
          v-for="(offer, index) in availableOffers"
          :id="`${id}-option-${index}`"
          :key="offer.id"
          type="button"
          role="option"
          tabindex="-1"
          :aria-selected="modelValue?.id === offer.id"
          :class="{ highlighted: index === highlightedIndex }"
          @mousedown.prevent
          @click="selectOffer(offer)"
        >
          <span class="offer-option">
            <span>{{ offer.name }}</span>
            <small>
              #{{ offer.id }}
              <span v-if="offer.country?.length">· {{ offer.country.join(', ') }}</span>
            </small>
          </span>
          <Check
            v-if="modelValue?.id === offer.id"
            :size="16"
          />
        </button>
      </template>
    </div>
  </div>
</template>
