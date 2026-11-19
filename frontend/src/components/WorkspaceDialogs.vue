<script setup lang="ts">
import type { HistoryEvent, Stream, SyncConflict } from '../types'
import { formatTime } from '../utils/format'
import Modal from './Modal.vue'

defineProps<{
  campaignNamePrefix: string
  helpOpen: boolean
  pendingCancel: Stream | null
  conflict: SyncConflict | null
  history: HistoryEvent[] | null
  disabled: boolean
  error: string
}>()
const emit = defineEmits<{
  closeHelp: []
  closeCancel: []
  closeConflict: []
  closeHistory: []
  confirmCancel: []
  discardAndFetch: []
}>()

const actionLabels: Record<string, string> = {
  fetch: 'Загрузка из Keitaro',
  create: 'Создание кампании',
  add: 'Добавление оффера',
  remove: 'Оффер перенесён в архив',
  restore: 'Восстановление оффера',
  pin: 'Доля закреплена',
  unpin: 'Доля откреплена',
  cancel: 'Черновик отменён',
  push: 'Публикация в Keitaro',
}
</script>

<template>
  <Modal
    v-if="helpOpen"
    title="Как работает Adrobot"
    @close="emit('closeHelp')"
  >
    <p>
      <strong>Создание кампании.</strong>
      Укажите название, гео, оффер и настройки Keitaro. Первый поток направит выбранные страны на
      Google, второй — на оффер. Кампания создаётся сразу в Keitaro и получает префикс
      <code>{{ campaignNamePrefix }}</code>
      .
    </p>
    <p>
      <strong>Редактор.</strong>
      Добавляйте, убирайте и возвращайте офферы. Доли пересчитываются до 100%. Закрепите долю
      кнопкой с булавкой или введите новое значение. Доли задаются целыми процентами; остаток
      распределяется по порядку незакреплённых офферов.
    </p>
    <p>
      <strong>Черновики.</strong>
      «Опубликовать» (Push to Keitaro) отправляет изменения в трекер. «Отменить» (Cancel) возвращает
      исходный снимок после подтверждения. Архивные офферы доступны для восстановления. До
      публикации изменения офферов хранятся локально и сохраняются после перезагрузки страницы.
    </p>
    <p>
      <strong>Синхронизация (Fetch streams).</strong>
      Загружает актуальное состояние. Если оффер удалён в Keitaro, он попадёт в местный архив.
      Неопубликованные черновики сохраняются до вашего решения.
    </p>
    <div class="help-connection">
      <h3>Подключение Keitaro</h3>
      <p>
        Приложение работает с реальным Keitaro. Адрес сервера и API-ключ задаются в
        <code>.env</code>
        через
        <code>KEITARO_URL</code>
        и
        <code>KEITARO_API_KEY</code>
        . После изменения настроек перезапустите backend.
      </p>
      <p>
        Ключ остаётся на backend. Все справочники и актуальные настройки загружаются из Keitaro. Для
        проверки внешних изменений нажмите «Синхронизировать».
      </p>
    </div>
    <button
      class="button primary"
      @click="emit('closeHelp')"
    >
      Понятно
    </button>
  </Modal>

  <Modal
    v-if="pendingCancel"
    title="Отменить изменения потока?"
    @close="emit('closeCancel')"
  >
    <p>
      Черновик потока «{{ pendingCancel.name }}» будет заменён последним опубликованным состоянием.
      Новые офферы, добавленные после загрузки, исчезнут из черновика.
    </p>
    <p
      v-if="error"
      class="error-text"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="modal-actions">
      <button
        class="button secondary"
        :disabled="disabled"
        @click="emit('closeCancel')"
      >
        Продолжить редактирование
      </button>
      <button
        class="button primary"
        :disabled="disabled"
        @click="emit('confirmCancel')"
      >
        Отменить черновик
      </button>
    </div>
  </Modal>

  <Modal
    v-if="conflict"
    title="Сверка с Keitaro"
    @close="emit('closeConflict')"
  >
    <p>В кампании есть локальные черновики. Они сохранены и ещё не опубликованы.</p>
    <div class="sync-changes">
      <strong>Состояние источника</strong>
      <ul v-if="conflict.changes.length">
        <li
          v-for="change in conflict.changes"
          :key="change"
        >
          {{ change }}
        </li>
      </ul>
      <p v-else>Состав и доли офферов в Keitaro не изменились.</p>
    </div>
    <p>
      Можно продолжить работу с черновиками или отменить их и загрузить текущую конфигурацию из
      Keitaro.
    </p>
    <p
      v-if="error"
      class="error-text"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="modal-actions">
      <button
        class="button secondary"
        :disabled="disabled"
        @click="emit('closeConflict')"
      >
        Сохранить черновики
      </button>
      <button
        class="button primary"
        :disabled="disabled"
        @click="emit('discardAndFetch')"
      >
        {{ disabled ? 'Загружаем…' : 'Отменить и загрузить' }}
      </button>
    </div>
  </Modal>

  <Modal
    v-if="history !== null"
    title="История действий"
    @close="emit('closeHistory')"
  >
    <p>Последние 100 действий в этой кампании. Время указано в вашем часовом поясе.</p>
    <ol
      v-if="history.length"
      class="history-list"
    >
      <li
        v-for="event in history"
        :key="event.id"
      >
        <span class="history-dot"></span>
        <div>
          <strong>{{ actionLabels[event.action] ?? event.action }}</strong>
          <small>
            <span v-if="event.stream_id">Поток #{{ event.stream_id }} ·</span>
            <span v-if="event.details.offer_id">Оффер #{{ event.details.offer_id }} ·</span>
            {{ formatTime(event.created_at) }}
          </small>
        </div>
      </li>
    </ol>
    <p v-else>Действий пока нет. Нажмите «Синхронизировать» для загрузки потоков.</p>
  </Modal>
</template>
