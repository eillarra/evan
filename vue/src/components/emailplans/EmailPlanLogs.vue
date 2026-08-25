<template>
  <emails-view :emails="logs" :tags="['emailplan.id:' + planId]" />
</template>

<script setup lang="ts">
import { shallowRef, watchEffect } from 'vue';

import { useStore } from '@/apps/event/store';

import EmailsView from '@/components/emails/EmailsView.vue';

const props = defineProps<{
  planId: number;
}>();

const store = useStore();
const logs = shallowRef<Email[]>([]);

watchEffect(async () => {
  logs.value = await store.fetchEmailPlanLogs(props.planId);
});
</script>
