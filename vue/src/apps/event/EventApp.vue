<template>
  <div class="row ugent__submenu q-mb-lg">
    <div v-if="evanEvents.length < 2" class="menu-item">
      <span>{{ currentEvent.name }}</span>
    </div>
    <q-select
      v-else
      dense
      borderless
      square
      options-dense
      v-model="selectedEventCode"
      :options="evanEvents"
      option-value="code"
      option-label="name"
      emit-value
      map-options
      hide-bottom-space
      :dropdown-icon="$q.iconSet.expansionItem.icon"
      popup-content-class="q-menu__square"
    >
      <template #selected-item>
        <span class="text-underline">{{ currentEvent.name }}</span>
      </template>
    </q-select>
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { usePage } from '@inertiajs/vue3';

import { useStore } from './store';

const page = usePage();
const store = useStore();

const evanEvents = computed<EvanEvent[]>(() => page.props.events as EvanEvent[]);
const currentEvent = computed<ManagedEvanEvent>(() => page.props.event as ManagedEvanEvent);
const selectedEventCode = ref<string>(currentEvent.value.code);

store.setData(currentEvent.value);

watch(selectedEventCode, (code: string) => {
  window.location.href = `../${code}/`;
});
</script>
