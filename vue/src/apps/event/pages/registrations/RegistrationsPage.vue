<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.registration', 9) }}
    </h3>
  </div>
  <!--<div class="row q-col-gutter-sm q-mb-lg">
    <div class="col"></div>
    <period-select
      as-filter
      :label="$t('availability')"
      :periods="periodOptions"
      v-model="selectedPeriod"
      class="col-6 col-md-2"
    />
    <place-option-select
      v-if="education?.place_locations.length"
      as-filter
      :label="$t('place_location')"
      :place-types="(education?.place_locations as PlaceLocation[])"
      v-model="selectedPlaceLocation"
      class="col-6 col-md-2"
    />
    <place-option-select
      v-if="education?.place_types.length"
      as-filter
      :label="$t('place_type')"
      :place-types="(education?.place_types as PlaceType[])"
      v-model="selectedPlaceType"
      class="col-6 col-md-2"
    />
    <q-select
      v-model="selectedDiscipline"
      :disable="!disciplineOptions.length"
      clearable
      dense
      rounded
      outlined
      :options="disciplineOptions"
      :label="$t('discipline')"
      options-dense
      emit-value
      map-options
      class="col-6 col-md-2"
      :bg-color="selectedDiscipline !== null ? 'blue-1' : 'white'"
    >
      <template #selected-item="scope">
        <span class="ellipsis">{{ scope.opt.label }}</span>
      </template>
    </q-select>
  </div>-->
  <registrations-table :registrations="filteredRegistrations" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store.js';

import RegistrationsTable from './RegistrationsTable.vue';

const store = useStore();

const { registrations } = storeToRefs(store);

const selectedDiscipline = ref<number | null>(null);
const selectedPeriod = ref<number | null>(null);
const selectedPlaceLocation = ref<number | null>(null);
const selectedPlaceType = ref<number | null>(null);

const filteredRegistrations = computed<Registration[]>(() => {
  return registrations.value;
});
</script>
