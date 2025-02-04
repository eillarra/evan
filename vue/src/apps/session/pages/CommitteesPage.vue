<template>
  <committees-tables v-if="session" v-model="session" />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../store';

import CommitteesTables from '@/components/extra_data/CommitteesTables.vue';

const store = useStore();

const { session } = storeToRefs(store);
</script>
