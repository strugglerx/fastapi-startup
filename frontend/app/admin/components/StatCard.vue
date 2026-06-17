<template>
  <n-card size="small" :bordered="false" class="!shadow-sm">
    <div class="space-y-1">
      <p class="text-[11px] font-medium uppercase tracking-wider text-slate-400">{{ label }}</p>
      <p class="font-mono text-3xl font-semibold" :class="toneClass">
        <span v-if="loading" class="text-slate-300">…</span>
        <span v-else>{{ formatted }}</span>
      </p>
      <p v-if="sub" class="text-[11px] text-slate-500">{{ sub }}</p>
    </div>
  </n-card>
</template>

<script setup>
import { computed } from "vue";
import { NCard } from "naive-ui";

const props = defineProps({
  label:   { type: String, required: true },
  value:   { type: [Number, String], required: true },
  sub:     { type: String, default: "" },
  tone:    { type: String, default: "slate" }, // slate | indigo | emerald | amber | sky | rose
  loading: { type: Boolean, default: false },
});

const TONE_CLASSES = {
  slate:   "text-slate-700",
  indigo:  "text-indigo-600",
  emerald: "text-emerald-600",
  amber:   "text-amber-600",
  sky:     "text-sky-600",
  rose:    "text-rose-600",
};

const toneClass = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.slate);

const formatted = computed(() => {
  if (typeof props.value !== "number") return props.value;
  if (props.value >= 1000) {
    return new Intl.NumberFormat("en-US").format(props.value);
  }
  return String(props.value);
});
</script>
