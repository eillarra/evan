<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.sponsor', 9) }}
    </h3>
  </div>
  <sponsors-table :sponsors="sponsors" />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import SponsorsTable from './SponsorsTable.vue';

const store = useStore();
const { sponsors } = storeToRefs(store);

onMounted(() => store.fetchSponsors());
</script>
