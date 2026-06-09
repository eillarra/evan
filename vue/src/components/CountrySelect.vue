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
  modelValue: CountryCode | CountryDict | null;
  asDict?: boolean;
}>();

function getCountryCode(modelValue: CountryCode | CountryDict | null): CountryCode {
  if (!modelValue) {
    return '';
  }

  return typeof modelValue === 'string' ? modelValue : modelValue.code;
}

const mutable = ref<CountryCode | CountryDict | null>(props.modelValue);
const countryCode = ref<CountryCode>(getCountryCode(props.modelValue));

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
  countryCode.value = getCountryCode(val);
  emit('update:modelValue', val);
});

watch(
  () => props.modelValue,
  (val) => {
    mutable.value = val;
    countryCode.value = getCountryCode(val);
  },
);
</script>
