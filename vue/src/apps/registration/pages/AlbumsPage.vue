<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('album', 9) }}
    </h3>
  </div>
  <album-viewer v-if="evanEvent && canViewAlbums" :event-code="evanEvent.code" :albums="albums" :loading="loading" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import AlbumViewer from '@/components/AlbumViewer.vue';

import { useStore } from '../store';

const store = useStore();
const { evanEvent, registration, albums } = storeToRefs(store);

const canViewAlbums = computed(() => registration.value?.is_accepted && !registration.value.no_show);

const loading = computed(() => false);
</script>
