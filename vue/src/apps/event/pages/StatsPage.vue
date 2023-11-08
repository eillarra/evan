<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('stats') }}
    </h3>
  </div>
  <div v-if="evanEvent">Coming soon...</div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../store';

const { evanEvent } = storeToRefs(useStore());
</script>
