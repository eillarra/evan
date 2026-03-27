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
  <div v-else-if="!evanEvent" class="row q-col-gutter-md">
    <div class="col-12 col-md-3" v-for="i in 4" :key="i">
      <stats-skeleton-card :items="3" />
    </div>
  </div>
  <div v-else class="flex items-center q-mt-md">
    <svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="#aaa">
      <path
        d="M275.38-304.62h169.24v-30.76H275.38v30.76Zm378.47 0h30.77v-30.76h-30.77v30.76Zm-378.47-160h169.24v-30.76H275.38v30.76Zm378.47 0h30.77v-190.76h-30.77v190.76Zm-378.47-160h169.24v-30.76H275.38v30.76ZM116.62-160v-640h726.76v640H116.62Zm30.76-30.77h665.24v-578.46H147.38v578.46Zm0 0v-578.46 578.46Z"
      />
    </svg>
    <span class="q-ml-sm text-grey-6">{{ $t('waiting_for_registrations') }}</span>
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
