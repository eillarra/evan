<style lang="scss">
.stats-card.q-card--bordered {
  border: 1px #888 dashed !important; // grey-4
}
</style>

<template>
  <q-card flat square bordered class="full-height column stats-card">
    <q-card-section>
      <div class="text-h6 q-mb-sm">
        <strong>{{ title }}</strong>
      </div>
      <div class="text-h4" :class="valueColor || 'text-grey-8'">{{ value }}</div>
    </q-card-section>
    <q-space />
    <q-list dense class="q-py-sm">
      <q-item v-for="(item, index) in items" :key="index">
        <q-item-section>
          <q-item-label>{{ item.label }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-item-label class="panno-mono-number" :class="item.color || 'text-dark'">{{ item.value }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-card>
</template>

<script setup lang="ts">
interface StatsItem {
  label: string;
  value: string;
  color?: string;
}

defineProps<{
  title: string;
  value: string;
  valueColor?: string;
  items: StatsItem[];
}>();
</script>
