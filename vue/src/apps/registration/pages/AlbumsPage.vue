<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('album', 9) }}
    </h3>
  </div>
  <album-viewer v-if="evanEvent && canViewAlbums" :event-code="evanEvent.code" :albums="albums" :loading="loading" />
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';

import AlbumViewer from '@/components/AlbumViewer.vue';
import { useAlbums } from '@/composables/useAlbums';

import { useStore } from '../store';

const store = useStore();
const { evanEvent, registration } = storeToRefs(store);
const { albums, loading, fetchAlbums } = useAlbums();

// Check if user can view albums (registered and not no-show)
const canViewAlbums = computed(() => {
  return registration.value && registration.value.is_accepted && !registration.value.no_show;
});

// Computed property to determine if we should fetch albums
const shouldFetchAlbums = computed(() => {
  return evanEvent.value?.code && canViewAlbums.value;
});

// Watch for changes in conditions and fetch albums when ready
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
  if (shouldFetchAlbums.value && evanEvent.value?.code) {
    fetchAlbums(evanEvent.value.code);
  }
});
</script>
