<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.session', 9) }}
    </h3>
    <div class="col"></div>
    <evan-filter-select
      v-if="dateOptions.length > 1"
      v-model="dateFilter"
      :options="dateOptions"
      :label="$t('fields.date')"
      clearable
    />
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
const dateFilter = ref<string | null>(null); // Value will be YYYY-MM-DD string

const dateOptions = computed(() => {
  if (!sessions.value) return [];
  const uniqueDates = new Set<string>();
  sessions.value.forEach((session) => {
    if (session.start_at) {
      const dateStr = new Date(session.start_at).toISOString().split('T')[0];
      uniqueDates.add(dateStr);
    }
  });
  return Array.from(uniqueDates)
    .sort()
    .map((dateStr, index) => {
      // dateStr is 'YYYY-MM-DD'
      // Parse numeric day and month to achieve D/M format (e.g., 5/6 instead of 05/06)
      const day = parseInt(dateStr.substring(8, 10), 10);
      const month = parseInt(dateStr.substring(5, 7), 10);
      return {
        label: `Day ${index + 1} - ${day}/${month}`,
        value: dateStr,
      };
    });
});

const filteredSessions = computed<Session[]>(() => {
  if (trackFilter.value === null && topicFilter.value === null && dateFilter.value === null) {
    return sessions.value;
  }

  return sessions.value.filter((session) => {
    if (trackFilter.value !== null && session.track !== trackFilter.value) {
      return false;
    }

    if (topicFilter.value !== null && (!session.topics || !session.topics.includes(topicFilter.value))) {
      return false;
    }

    if (dateFilter.value !== null) {
      if (!session.start_at) return false;
      const sessionDate = new Date(session.start_at).toISOString().split('T')[0];
      if (sessionDate !== dateFilter.value) {
        return false;
      }
    }

    return true;
  });
});

onMounted(() => store.fetchSessions());
</script>
