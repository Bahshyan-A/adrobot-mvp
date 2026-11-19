<script setup lang="ts">
import { Layers, Pin, RotateCcw, Trash2 } from 'lucide-vue-next'
import type { Offer, OfferMutation } from '../types'

defineProps<{ offers: Offer[]; disabled: boolean }>()
const emit = defineEmits<{ mutate: [mutation: OfferMutation] }>()

function setShare(event: Event, offer: Offer): void {
  const input = event.target as HTMLInputElement
  if (!input.reportValidity()) {
    input.value = String(offer.share)
    return
  }
  const share = Number(input.value)
  const isValid = input.value !== '' && Number.isInteger(share) && share >= 0 && share <= 100

  // Reset the field until the server confirms the new draft.
  input.value = String(offer.share)
  if (isValid) {
    emit('mutate', { action: 'pin', offer_id: offer.offer_id, share })
  }
}
</script>

<template>
  <div class="offer-table-scroll">
    <table class="offer-table">
      <thead>
        <tr>
          <th scope="col">Оффер</th>
          <th
            scope="col"
            class="share-heading"
          >
            Доля трафика
          </th>
          <th
            scope="col"
            class="actions-heading"
          >
            Действия
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="offer in offers"
          :key="offer.offer_id"
          :class="{ removed: offer.removed }"
        >
          <td>
            <div class="offer-cell">
              <span class="offer-table-icon"><Layers :size="17" /></span>
              <div>
                <strong>{{ offer.name }}</strong>
                <small>
                  #{{ offer.offer_id }}
                  <span
                    v-if="offer.removed"
                    class="inline-status"
                  >
                    {{ offer.removed_reason === 'source' ? 'Удалён в Keitaro' : 'В архиве' }}
                  </span>
                  <span
                    v-else-if="offer.new"
                    class="inline-status new"
                  >
                    Новый
                  </span>
                  <span
                    v-else-if="offer.state === 'disabled'"
                    class="inline-status"
                  >
                    Отключён в Keitaro
                  </span>
                </small>
              </div>
            </div>
          </td>
          <td>
            <div class="share-control">
              <span
                v-if="offer.removed"
                class="removed-share"
              >
                0
                <span>%</span>
              </span>
              <template v-else>
                <div class="percent-input">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    :aria-label="`Доля оффера ${offer.offer_id}`"
                    :value="offer.share"
                    :disabled="disabled"
                    @change="setShare($event, offer)"
                  />
                  <span>%</span>
                </div>
                <button
                  class="icon-button pin-button"
                  :class="{ pinned: offer.pinned }"
                  :aria-label="`${offer.pinned ? 'Открепить' : 'Закрепить'} долю оффера ${offer.offer_id}`"
                  :aria-pressed="offer.pinned"
                  :title="offer.pinned ? 'Открепить долю' : 'Закрепить долю'"
                  :disabled="disabled"
                  @click="
                    emit('mutate', {
                      action: offer.pinned ? 'unpin' : 'pin',
                      offer_id: offer.offer_id,
                    })
                  "
                >
                  <Pin :size="15" />
                </button>
              </template>
            </div>
          </td>
          <td>
            <button
              v-if="offer.removed"
              class="restore-button"
              :disabled="disabled"
              @click="emit('mutate', { action: 'restore', offer_id: offer.offer_id })"
            >
              <RotateCcw :size="14" />
              Вернуть
            </button>
            <button
              v-else
              class="icon-button remove-button"
              :disabled="disabled"
              :aria-label="`Удалить оффер ${offer.offer_id}`"
              title="Убрать из потока"
              @click="emit('mutate', { action: 'remove', offer_id: offer.offer_id })"
            >
              <Trash2 :size="16" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
