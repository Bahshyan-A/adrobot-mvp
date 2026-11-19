<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { X } from 'lucide-vue-next'

defineProps<{ title: string }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement>()

function closeOnBackdrop(event: MouseEvent): void {
  if (event.target === event.currentTarget) emit('close')
}

onMounted(() => dialog.value?.showModal())
onBeforeUnmount(() => dialog.value?.close())
</script>

<template>
  <dialog
    ref="dialog"
    class="native-dialog"
    :aria-label="title"
    @cancel.prevent="emit('close')"
    @click="closeOnBackdrop"
  >
    <section class="help-modal panel">
      <button
        class="icon-button modal-close"
        type="button"
        autofocus
        aria-label="Закрыть диалог"
        @click="emit('close')"
      >
        <X :size="20" />
      </button>
      <h2>{{ title }}</h2>
      <slot />
    </section>
  </dialog>
</template>
