<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.materials') }}
    </h3>
    <div class="col-12">
      <files-view v-if="filesEndpoint" :api-endpoint="filesEndpoint" :secret="secret ?? ''" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../store';

import FilesView from '@/components/rel/FilesView.vue';

const store = useStore();
const { session, secret } = storeToRefs(store);

const filesEndpoint = computed(() => session.value?.rel_files ?? '');
</script>
