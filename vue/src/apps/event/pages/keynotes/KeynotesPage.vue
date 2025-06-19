<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.keynote', 9) }}
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
  <keynotes-table :keynotes="filteredKeynotes" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import KeynotesTable from './KeynotesTable.vue';

const store = useStore();

const { keynotes, topicOptions, trackOptions, sessions } = storeToRefs(store);

const topicFilter = ref<number | null>(null);
const trackFilter = ref<number | null>(null);

const filteredKeynotes = computed<Keynote[]>(() => {
  if (trackFilter.value === null && topicFilter.value === null) {
    return keynotes.value;
  }

  return keynotes.value.filter((keynote) => {
    // Filter by track through session.track relationship
    if (trackFilter.value !== null) {
      if (!keynote.session) return false;

      const session = sessions.value.find((s) => s.id === keynote.session);
      if (!session || session.track !== trackFilter.value) {
        return false;
      }
    }

    if (topicFilter.value !== null && (!keynote.topics || !keynote.topics.includes(topicFilter.value))) {
      return false;
    }

    return true;
  });
});

onMounted(() => store.fecthProgramData());
</script>
