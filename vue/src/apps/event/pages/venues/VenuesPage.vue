<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.venues_rooms') }}
    </h3>
  </div>

  <div v-if="evanEvent">
    <VenuesTable :venues="evanEvent.venues" />
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';
import VenuesTable from './VenuesTable.vue';

const { evanEvent } = storeToRefs(useStore());
</script>
