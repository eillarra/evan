<template>
  <q-select
    v-model="mutable"
    :label="label"
    :options="options"
    :dense="!notDense"
    :options-dense="!notDense"
    emit-value
    map-options
    :multiple="multiple"
  >
    <template #selected-item="scope">
      <span class="ellipsis">{{ scope.opt.label }}</span>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: string | number | boolean | null | (string | number)[];
  options: { label: string; value: string | number | boolean | null }[];
  multiple?: boolean;
  notDense?: boolean;
}>();

const mutable = ref<string | number | boolean | null | (string | number)[]>(props.modelValue);

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
