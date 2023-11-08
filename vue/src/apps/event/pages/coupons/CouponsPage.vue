<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.coupon', 9) }}
    </h3>
    <div class="col"></div>
    <evan-filter-select v-model="couponFilter" :options="couponFilterOptions" :label="$t('fields.used')" />
  </div>
  <coupons-table :coupons="filteredCoupons" :coupon-ids-used="couponIdsUsed" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store.js';

import CouponsTable from './CouponsTable.vue';

const store = useStore();

const { coupons, couponIdsUsed } = storeToRefs(store);

const couponFilter = ref<boolean | null>(null);
const couponFilterOptions = computed(() => {
  return [
    { label: 'Yes', value: true },
    { label: 'No', value: false },
  ];
});

const filteredCoupons = computed<Coupon[]>(() => {
  if (couponFilter.value === null) {
    return coupons.value;
  }
  return coupons.value.filter((coupon) => {
    return couponFilter.value === couponIdsUsed.value.has(coupon.id);
  });
});

onMounted(() => store.fetchCoupons());
</script>
