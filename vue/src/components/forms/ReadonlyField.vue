<template>
  <q-field :label="label" readonly dense stack-label class="col">
    <template #control>
      <div class="self-center full-width no-outline ellipsis" tabindex="0">{{ value }}</div>
    </template>
    <template #append>
      <copy-icon v-if="withCopy" :text="value" class="q-mt-md" />
    </template>
  </q-field>
</template>

<script setup lang="ts">
import CopyIcon from '@/components/CopyIcon.vue';

defineProps<{
  label: string;
  value: string | number;
  withCopy?: boolean;
}>();
</script>
