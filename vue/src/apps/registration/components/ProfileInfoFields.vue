<template>
  <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
    <q-input v-model="user.first_name" :label="$t('fields.first_name') + ' *'" dense class="col-12 col-md-6" />
    <q-input v-model="user.last_name" :label="$t('fields.last_name') + ' *'" dense class="col-12 col-md-6" />
    <q-input v-model="user.affiliation" :label="$t('fields.affiliation') + ' *'" dense class="col-12 col-md-6" />
    <country-select v-model="user.country" :label="$t('fields.country') + ' *'" class="col-12 col-md-6" />
    <gender-select v-model="user.extra_data.gender" class="col-12" />
  </div>
</template>

<script setup lang="ts">
import CountrySelect from '@/components/CountrySelect.vue';
import GenderSelect from '@/components/GenderSelect.vue';

const user = defineModel<AuthenticatedUser>('user', { required: true });
</script>
