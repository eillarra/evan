<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('album', 9) }}
    </h3>
  </div>
  <album-viewer v-if="evanEvent" :event-code="evanEvent.code" :albums="albums" :loading="loading" />
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';

import AlbumViewer from '@/components/AlbumViewer.vue';
import { useAlbums } from '@/composables/useAlbums';
import { useStore } from '../../store';

const { evanEvent } = storeToRefs(useStore());
const { albums, loading, fetchAlbums } = useAlbums();

// Computed property to determine if we should fetch albums
const shouldFetchAlbums = computed(() => {
  return !!evanEvent.value?.code;
});

// Watch for changes in evanEvent and fetch albums when ready
watch(
  shouldFetchAlbums,
  (shouldFetch) => {
    if (shouldFetch && evanEvent.value?.code) {
      fetchAlbums(evanEvent.value.code);
    }
  },
  { immediate: true },
);

onMounted(() => {
  if (evanEvent.value?.code) {
    fetchAlbums(evanEvent.value.code);
  }
});
</script>
