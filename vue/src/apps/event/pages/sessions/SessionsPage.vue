<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.session', 9) }}
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
  <sessions-table :sessions="filteredSessions" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import SessionsTable from './SessionsTable.vue';

const store = useStore();

const { sessions, topicOptions, trackOptions } = storeToRefs(store);

const topicFilter = ref<number | null>(null);
const trackFilter = ref<number | null>(null);

const filteredSessions = computed<Session[]>(() => {
  if (trackFilter.value === null && topicFilter.value === null) {
    return sessions.value;
  }

  return sessions.value.filter((session) => {
    if (trackFilter.value !== null && session.track !== trackFilter.value) {
      return false;
    }

    if (topicFilter.value !== null && (!session.topics || !session.topics.includes(topicFilter.value))) {
      return false;
    }

    return true;
  });
});

onMounted(() => store.fetchSessions());
</script>
