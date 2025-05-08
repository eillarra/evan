<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.registration', 9) }}
    </h3>
  </div>
  <q-list>
    <q-item v-for="registration in registrations" :key="registration.uuid" clickable :href="registration.url">
      <q-item-section>
        <q-item-label>{{ registration.event.name }}</q-item-label>
        <q-item-label caption>{{ registration.event.full_name }}</q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

const page = usePage();

const registrations = computed<Registration[]>(() => {
  return page.props.registrations as Registration[];
});
</script>
