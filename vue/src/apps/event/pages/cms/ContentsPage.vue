<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.content', 9) }}
    </h3>
  </div>
  <contents-table :contents="contents" />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import ContentsTable from './ContentsTable.vue';

const store = useStore();

const { contents } = storeToRefs(store);

onMounted(() => store.fetchContents());
</script>
