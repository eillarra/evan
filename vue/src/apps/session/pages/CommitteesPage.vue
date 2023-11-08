<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.committee', 9) }}
    </h3>
  </div>
  <div v-if="session" class="row q-col-gutter-xl">
    <persons-table v-model="session" field="chairs" title="Chairs" class="col-12 col-md-6" />
    <persons-table v-model="session" field="program_commitee" title="Program Commitee" class="col-12 col-md-6" />
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../store';

import PersonsTable from '@/components/extra_data/PersonsTable.vue';

const store = useStore();

const { session } = storeToRefs(store);

function update() {
  store.updateSession();
}
</script>
