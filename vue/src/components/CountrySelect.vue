<template>
  <q-select
    dense
    :label="label"
    v-model="mutable"
    :options="options"
    options-dense
    option-value="code"
    option-label="name"
    emit-value
    map-options
  >
    <template v-slot:append>
      <country-flag :code="mutable" />
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';

import CountryFlag from './CountryFlag.vue';
import { useCommonStore } from '@/stores/common';

const commonStore = useCommonStore();

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: string;
}>();

const mutable = ref<string>(props.modelValue);
const { countries } = storeToRefs(commonStore);

const options = computed(() => {
  if (!countries.value) {
    return [];
  }

  return Object.entries(countries.value as CountryMap).map(([key, val]) => {
    return {
      code: key,
      name: val,
    };
  });
});

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
