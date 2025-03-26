<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none">{{ $t('fields.email', 9) }}</h3>
  </div>
  <emails-view :emails="emails" />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../../store.js';

import EmailsView from '@/components/emails/EmailsView.vue';

const store = useStore();

const { emails } = storeToRefs(store);
</script>
