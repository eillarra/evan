<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.paper', 9) }}
    </h3>
    <div class="col"></div>
    <evan-filter-select
      v-if="trackOptions.length"
      v-model="trackFilter"
      :options="trackOptions"
      :label="$t('models.track')"
    />
    <evan-filter-select
      v-if="topicOptions.length"
      v-model="topicFilter"
      :options="topicOptions"
      :label="$t('models.topic')"
    />
  </div>
  <papers-table :papers="filteredPapers" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import PapersTable from './PapersTable.vue';

const store = useStore();

const { papers, topicOptions, trackOptions, sessions } = storeToRefs(store);

const topicFilter = ref<number | null>(null);
const trackFilter = ref<number | null>(null);

const filteredPapers = computed<Paper[]>(() => {
  if (trackFilter.value === null && topicFilter.value === null) {
    return papers.value;
  }

  return papers.value.filter((paper) => {
    // Filter by track through session.track relationship
    if (trackFilter.value !== null) {
      if (!paper.session) return false;

      const session = sessions.value.find((s) => s.id === paper.session);
      if (!session || session.track !== trackFilter.value) {
        return false;
      }
    }

    if (topicFilter.value !== null && (!paper.topics || !paper.topics.includes(topicFilter.value))) {
      return false;
    }

    return true;
  });
});

onMounted(() => store.fetchProgramData());
</script>
