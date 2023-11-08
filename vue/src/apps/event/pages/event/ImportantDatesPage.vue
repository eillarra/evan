<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.important_date', 9) }}
    </h3>
  </div>
  <important-dates-table v-if="evanEvent" v-model="evanEvent">
    <template #banner>
      These dates are just informative and have no real effect on how Evan will work. Don't forget to change the event
      settings too if you want to change registration dates/deadlines.
    </template>
  </important-dates-table>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import ImportantDatesTable from '@/components/extra_data/ImportantDatesTable.vue';

const { evanEvent } = storeToRefs(useStore());
</script>
