<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('stats') }}
    </h3>
    <div class="col"></div>
    <q-select
      v-if="!isFreeEvent"
      v-model="activeTab"
      :options="panelOptions"
      dense
      rounded
      outlined
      label="Panel"
      options-dense
      emit-value
      map-options
      class="col-6 col-md-2"
      :bg-color="'blue-1'"
    />
  </div>
  <div v-if="evanEvent && registrations.length > 0">
    <attendees-panel v-if="isFreeEvent" />
    <financial-panel v-else-if="activeTab === 'financial'" />
    <attendees-panel v-else-if="activeTab === 'attendees'" />
  </div>
  <div v-else class="row q-col-gutter-md">
    <div class="col-12 col-md-3" v-for="i in 4" :key="i">
      <stats-skeleton-card :items="3" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import StatsSkeletonCard from '../../components/StatsSkeletonCard.vue';
import FinancialPanel from './FinancialPanel.vue';
import AttendeesPanel from './AttendeesPanel.vue';

const { evanEvent, registrations } = storeToRefs(useStore());

const activeTab = ref<string>('financial');

const isFreeEvent = computed(() => {
  if (!evanEvent.value?.fees || evanEvent.value.fees.length === 0) {
    return false;
  }

  return evanEvent.value.fees.every((fee) => {
    const regularValue = fee.value || 0;
    const earlyValue = fee.early_value || 0;
    return regularValue === 0 && earlyValue === 0;
  });
});

const panelOptions = computed(() => [
  {
    label: 'Financial',
    value: 'financial',
  },
  {
    label: 'Attendees',
    value: 'attendees',
  },
]);
</script>
