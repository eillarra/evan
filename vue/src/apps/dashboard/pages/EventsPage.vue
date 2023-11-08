<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.event', 9) }}
    </h3>
  </div>
  <q-list>
    <q-item v-for="event in managedEvents" :key="event.id" clickable :href="`/e/${event.code}/`">
      <q-item-section>
        <q-item-label>{{ event.name }}</q-item-label>
        <q-item-label caption>{{ event.full_name }}</q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

const page = usePage();

const managedEvents = computed<ManagedEvanEvent[]>(() => {
  return page.props.managed_events as ManagedEvanEvent[];
});
</script>
