<template>
  <div>
    <p>
      If you are bringing accompanying persons, please provide their name and dietary requirements. We will print a
      badge for them so they can join you during the social events.
    </p>

    <div v-if="modelValue.length === 0" class="text-grey q-my-md">No accompanying persons added.</div>

    <q-card flat v-for="(person, index) in modelValue" :key="index" class="bg-grey-1 q-mb-lg q-pa-md">
      <div class="row q-col-gutter-y-sm use-default-q-btn">
        <q-input v-model="person.name" label="Full Name *" dense class="col-12">
          <template #append>
            <q-btn :icon="iconDelete" color="negative" @click="removePerson(index)" round dense flat />
          </template>
        </q-input>
        <dietary-select v-model="person.dietary" label="Dietary Requirements" class="col-12" />
      </div>

      <p class="q-mt-lg">Social events this person will attend:</p>
      <q-list dense>
        <q-item v-for="event in socialEvents" :key="event.id" tag="label">
          <q-item-section avatar>
            <q-checkbox v-model="person.selected_social_events" :val="event.id" keep-color />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ event.title }}</q-item-label>
            <q-item-label caption>{{ formatDate(event.start_at || '', 'dddd, MMMM D, YYYY') }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-badge color="primary" :label="`+ € ${event.extra_attendees_fee || 0}`" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>

    <div class="row justify-start q-mt-md">
      <q-btn :icon="iconAdd" label="Add accompanying person" color="primary" flat @click="addPerson" />
    </div>

    <div v-if="totalAdditionalFee > 0" class="bg-blue-1 text-black q-my-md q-pa-md">
      <q-badge class="float-right text-body1 text-white text-weight-bold">€ {{ totalAdditionalFee }}</q-badge>
      <small>Additional fee for accompanying persons</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { formatDate } from '@/utils/dates';

import DietarySelect from '@/components/DietarySelect.vue';

import { iconAdd, iconDelete } from '@/icons';

const props = defineProps<{
  modelValue: AccompanyingPerson[];
  socialEvents: Session[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: AccompanyingPerson[]): void;
}>();

function addPerson() {
  const newPersons = [...props.modelValue, { name: '', selected_social_events: [], dietary: 'none' as DietaryOption }];
  emit('update:modelValue', newPersons);
}

function removePerson(index: number) {
  const newPersons = [...props.modelValue];
  newPersons.splice(index, 1);
  emit('update:modelValue', newPersons);
}

// Calculate total additional fee for all accompanying persons
const totalAdditionalFee = computed<number>(() => {
  let total = 0;

  for (const person of props.modelValue) {
    for (const eventId of person.selected_social_events) {
      const event = props.socialEvents.find((e) => e.id === eventId);
      if (event) {
        total += event.extra_attendees_fee;
      }
    }
  }

  return total;
});
</script>
