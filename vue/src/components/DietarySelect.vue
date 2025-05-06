<template>
  <q-select
    dense
    label="Dietary requirements"
    v-model="mutable"
    :options="options"
    options-dense
    emit-value
    map-options
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

interface DietarySelectOption {
  value: DietaryOption;
  label: string;
}

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: string;
}>();

const mutable = ref<string>(props.modelValue);

const options = computed<DietarySelectOption[]>(() => {
  return [
    {
      value: 'none',
      label: 'No special requirements',
    },
    {
      value: 'vegetarian',
      label: 'Vegetarian',
    },
    {
      value: 'vegan',
      label: 'Vegan',
    },
    {
      value: 'gluten_free',
      label: 'Gluten free',
    },
    {
      value: 'dairy_free',
      label: 'Dairy free',
    },
    {
      value: 'nut_free',
      label: 'Nut free',
    },
    {
      value: 'other',
      label: 'Other',
    },
  ];
});

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
