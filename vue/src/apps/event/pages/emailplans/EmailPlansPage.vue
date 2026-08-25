<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">{{ $t('models.email_plan', 2) }}</h3>
  </div>
  <email-plans-view :plans="emailPlans" />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import EmailPlansView from '@/components/emailplans/EmailPlansView.vue';

const store = useStore();

const { emailPlans } = storeToRefs(store);

onMounted(() => {
  store.fetchEmailPlans();
  store.fetchRegistrations();
  if (store.sessions.length === 0) {
    store.fetchSessions();
  }
});
</script>
