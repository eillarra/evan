<template>
  <q-select
    dense
    :label="label"
    v-model="mutable"
    :options="options"
    options-dense
    option-value="code"
    option-label="name"
    :emit-value="!asDict"
    :map-options="!asDict"
  >
    <template v-slot:append>
      <country-flag :code="countryCode" />
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';

import CountryFlag from './CountryFlag.vue';
import { useCommonStore } from '@/stores/common';

type CountryMap = Record<string, string>;

const commonStore = useCommonStore();

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: CountryCode | CountryDict;
  asDict?: boolean;
}>();

const mutable = ref<CountryCode | CountryDict>(props.modelValue);
const countryCode = ref<CountryCode>(typeof props.modelValue === 'string' ? props.modelValue : props.modelValue.code);

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
