<template>
  <div class="row q-col-gutter-x-xl">
    <h3 class="text-ugent col-12">My profile</h3>
    <div v-if="user" class="col-12 col-md-7">
      <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
        <q-input v-model="user.first_name" :label="$t('fields.first_name') + ' *'" dense class="col-12 col-md-6" />
        <q-input v-model="user.last_name" :label="$t('fields.last_name') + ' *'" dense class="col-12 col-md-6" />
        <q-input v-model="user.affiliation" :label="$t('fields.affiliation') + ' *'" dense class="col-12 col-md-6" />
        <country-select v-model="user.country" :label="$t('fields.country') + ' *'" class="col-12 col-md-6" />
        <gender-select v-model="user.extra_data.gender" class="col-12" />
        <dietary-select v-model="user.extra_data.dietary" class="col-12" />
      </div>
      <ugent-btn
        @click="saveProfile"
        :label="$t('form.update')"
        color="primary"
        class="q-mt-xl"
        :disable="!formIsValid"
      />
      <q-space class="q-mb-xl" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useUserStore } from '@/stores/user';

import CountrySelect from '@/components/CountrySelect.vue';
import DietarySelect from '@/components/DietarySelect.vue';
import GenderSelect from '@/components/GenderSelect.vue';

const userStore = useUserStore();

const { user } = storeToRefs(userStore);

function saveProfile() {
  if (user.value) {
    userStore.updateUser({
      first_name: user.value.first_name,
      last_name: user.value.last_name,
      affiliation: user.value.affiliation,
      country: user.value.country,
      extra_data: user.value.extra_data,
    });
  }
}

const formIsValid = computed<boolean>(() => {
  if (
    !user.value ||
    !user.value.first_name ||
    !user.value.last_name ||
    !user.value.affiliation ||
    !user.value.country
  ) {
    return false;
  }

  return true;
});
</script>
