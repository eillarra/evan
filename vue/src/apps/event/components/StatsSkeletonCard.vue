<style lang="scss">
.stats-card.q-card--bordered {
  border: 1px #888 dashed !important; // grey-4
}
</style>

<template>
  <q-card flat square bordered class="full-height column stats-card">
    <q-card-section>
      <div class="text-h6 q-mb-sm">
        <q-skeleton type="text" width="80%" />
      </div>
      <q-skeleton type="text" width="60%" height="50px" />
    </q-card-section>
    <q-space />
    <q-list dense class="q-py-sm">
      <q-item v-for="i in items" :key="i">
        <q-item-section>
          <q-item-label><q-skeleton type="text" width="100%" height="10px" /></q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-card>
</template>

<script setup lang="ts">
defineProps<{
  items: number;
}>();
</script>
