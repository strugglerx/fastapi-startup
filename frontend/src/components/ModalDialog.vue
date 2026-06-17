<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-220 ease-out"
      leave-active-class="transition-opacity duration-180 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="open" class="fixed inset-0 z-[210] bg-slate-900/60 p-4 backdrop-blur-sm" @click="$emit('close')"></div>
    </Transition>

    <Transition
      enter-active-class="transition-all duration-240 ease-out"
      leave-active-class="transition-all duration-180 ease-in"
      enter-from-class="opacity-0 scale-[0.98] translate-y-1"
      leave-to-class="opacity-0 scale-[0.98] translate-y-1"
    >
      <div v-if="open" class="fixed inset-0 z-[211] flex items-center justify-center p-4" @click.self="$emit('close')">
        <div :class="['flex w-full flex-col overflow-hidden rounded-3xl bg-white shadow-2xl', panelClass]" @click.stop>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  panelClass: { type: String, default: "h-[88vh] max-w-5xl" }
});

defineEmits(["close"]);
</script>
