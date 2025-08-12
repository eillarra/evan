<template>
  <div v-if="!loading" class="row justify-between q-col-gutter-x-xl">
    <h3 class="text-ugent col-12">
      <span v-if="registration">My registration</span>
      <span v-else>New registration</span>
    </h3>
    <div v-if="registration" class="col-12 col-md-7">
      <div v-if="user" class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
        <readonly-field
          :value="`${user.first_name} ${user.last_name}`"
          :label="$t('fields.name')"
          class="col-12 col-md-6"
        />
        <readonly-field :value="user.email" :label="$t('fields.email')" class="col-12 col-md-6" />
        <readonly-field :value="user.affiliation" :label="$t('fields.affiliation')" class="col-12 col-md-6" />
        <readonly-field :value="user.country" :label="$t('fields.country')" class="col-12 col-md-6" />
      </div>

      <evan-section-title>Registration information</evan-section-title>
      <div class="row q-col-gutter-y-sm">
        <readonly-field :value="registration.uuid" :label="$t('fields.code')" class="col-12" with-copy />
        <readonly-field :value="registration.updated_at" :label="$t('fields.updated_at')" class="col-12" />
      </div>

      <q-space class="q-mb-xl" />
    </div>
    <div class="col-12 col-md-4">
      <downloads-card :event-is-closed="evanEvent?.is_closed" :registration="registration" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useUserStore } from '@/stores/user';
import { useStore } from '../store';

import ReadonlyField from '@/components/forms/ReadonlyField.vue';
import DownloadsCard from '../../registration/components/DownloadsCard.vue';

const userStore = useUserStore();
const store = useStore();

const { user } = storeToRefs(userStore);
const { loading, registration, evanEvent } = storeToRefs(store);
</script>
