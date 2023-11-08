<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.important_date', 9) }}
    </h3>
  </div>
  <important-dates-table v-if="session" v-model="session" />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../store';

import ImportantDatesTable from '@/components/extra_data/ImportantDatesTable.vue';

const { session } = storeToRefs(useStore());
</script>
