<template>
  <div class="row">
    <h3 class="text-ugent col-12">
      <span v-if="registration">My registration</span>
      <span v-else>New registration</span>
    </h3>
    <div v-if="mutableRegistration" class="col-12 col-md-8">
      <div v-if="user" class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
        <readonly-field
          :value="`${user.first_name} ${user.last_name}`"
          :label="$t('fields.name')"
          class="col-12 col-md-6"
        />
        <readonly-field :value="user.email" :label="$t('fields.email')" class="col-12 col-md-6" />
        <q-input v-model="user.affiliation" :label="$t('fields.affiliation') + ' *'" dense class="col-12 col-md-6" />
        <country-select v-model="user.country" :label="$t('fields.country') + ' *'" class="col-12 col-md-6" />
        <gender-select v-model="user.extra_data.gender" class="col-12" />
      </div>

      <evan-section-title>Registration fee</evan-section-title>
      <fee-form-component
        v-if="evanEvent?.registration_configuration?.fee_selection"
        v-model:fee="mutableRegistration.fee_type"
        v-model:extraData="mutableRegistration.extra_data"
        :fee-config="evanEvent?.registration_configuration?.fee_selection"
      />
      <q-select
        v-else
        v-model="mutableRegistration.fee_type"
        :options="feeOptions"
        label="Fee"
        dense
        options-dense
        class="col-12"
        map-options
        emit-value
      />
      <p v-if="selectedFee" class="bg-blue-1 text-black q-my-md q-pa-md">
        <q-badge class="float-right text-body1 text-white text-weight-bold">€ {{ selectedFee.value }}</q-badge>
        <small>{{ selectedFee.notes }}</small>
      </p>

      <template v-if="user">
        <evan-section-title>Special needs</evan-section-title>
        <p>
          The following information will only be used to provide you with a better experience during physical events. We
          will <strong>never</strong> share your personal information with third parties.
        </p>
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
          <dietary-select v-model="user.extra_data.dietary" class="col-12" />
          <q-input
            v-model="user.extra_data.special_needs"
            label="Any other special needs (dietary, access restrictions, etc)?"
            dense
            class="col-12"
          />
        </div>
      </template>

      <evan-section-title>Travel visa</evan-section-title>
      <q-item class="q-pl-none" tag="label">
        <q-item-section avatar class="q-px-none">
          <q-checkbox v-model="mutableRegistration.visa_requested" keep-color />
        </q-item-section>
        <q-item-section>
          <q-item-label>I require an Invitation Letter for my visa application</q-item-label>
        </q-item-section>
      </q-item>

      <template v-if="registration">
        <evan-section-title class="q-mt-lg">Registration information</evan-section-title>
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start">
          <readonly-field :value="registration.uuid" :label="$t('fields.code')" class="col-12 col-md" with-copy />
          <readonly-field :value="registration.updated_at" :label="$t('fields.updated_at')" class="col-12 col-md" />
        </div>
      </template>

      <q-btn
        @click="saveRegistration"
        :label="registration ? $t('form.update') : $t('form.create')"
        color="primary"
        class="q-mt-xl"
        :disable="!formIsValid"
      />
      <q-space class="q-mb-xl" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';

import { useUserStore } from '@/stores/user';
import { useStore } from '../store';

import CountrySelect from '@/components/CountrySelect.vue';
import DietarySelect from '@/components/DietarySelect.vue';
import GenderSelect from '@/components/GenderSelect.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';
import FeeFormComponent from '../components/FeeFormComponent.vue';

const userStore = useUserStore();
const store = useStore();

const { user } = storeToRefs(userStore);
const { evanEvent, registration } = storeToRefs(store);

const mutableRegistration = ref<RegistrationData | undefined>(undefined);
const selectedFee = computed<Fee | undefined>(() => {
  return evanEvent.value?.fees.find((f: Fee) => f.type === mutableRegistration.value?.fee_type) || undefined;
});

const feeOptions = computed<QuasarSelectOption[]>(() => {
  if (!evanEvent.value?.registration_configuration?.fee_selection) {
    return [];
  }

  return evanEvent.value.fees.map((f: Fee) => ({
    value: f.type,
    label: f.notes,
  }));
});

function saveRegistration() {
  if (mutableRegistration.value) {
    if (registration.value) {
      store.updateRegistration(mutableRegistration.value);
    } else {
      store.createRegistration(mutableRegistration.value);
    }
  }

  if (user.value) {
    userStore.updateUser({
      affiliation: user.value.affiliation,
      country: user.value.country,
      extra_data: user.value.extra_data,
    });
  }
}

const feeExtraDataIsValid = computed<boolean>(() => {
  if (!evanEvent.value?.registration_configuration?.fee_selection) {
    return true;
  }

  const feeConfig = evanEvent.value.registration_configuration.fee_selection;

  if (!feeConfig || !feeConfig.criteria) {
    return true;
  }

  for (const criteria of feeConfig.criteria) {
    if (criteria.extra_data_fields) {
      const criteriaIndex = feeConfig.criteria.findIndex((c) => c.code === criteria.code);
      const selectedValue = mutableRegistration.value?.fee_type?.split('__')[criteriaIndex];

      for (const field of criteria.extra_data_fields) {
        const shouldShow =
          !field.show_for || field.show_for.length === 0 || field.show_for.includes(selectedValue as string);

        if (shouldShow && field.required && !mutableRegistration.value?.extra_data?.[field.code]) {
          return false;
        }
      }
    }
  }

  return true;
});

const formIsValid = computed<boolean>(() => {
  if (!mutableRegistration.value || !selectedFee.value) {
    return false;
  }

  return feeExtraDataIsValid.value;
});

watch(
  () => registration.value,
  (val) => {
    if (val) {
      mutableRegistration.value = val;
    } else {
      mutableRegistration.value = {
        fee_type: '',
        extra_data: {},
        visa_requested: false,
      };
    }
  },
  { immediate: true },
);
</script>
