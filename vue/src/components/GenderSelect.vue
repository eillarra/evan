<template>
  <q-select dense label="Gender" v-model="mutable" :options="options" options-dense emit-value map-options />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { GENDER_OPTIONS } from '@/utils/gender';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: string;
}>();

const mutable = ref<string>(props.modelValue);

const options = computed<QuasarSelectOption[]>(() => {
  return GENDER_OPTIONS.map((option) => ({
    value: option.value,
    label: option.label,
  }));
});

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
