<template>
  <q-select dense label="Gender" v-model="mutable" :options="options" options-dense emit-value map-options />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: string;
}>();

const mutable = ref<string>(props.modelValue);

const options = computed<QuasarSelectOption[]>(() => {
  return [
    {
      value: 'male',
      label: 'Male',
    },
    {
      value: 'female',
      label: 'Female',
    },
    {
      value: 'non_binary',
      label: 'Non-binary',
    },
    {
      value: 'prefer_not_to_say',
      label: 'Prefer not to say',
    },
  ];
});

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
