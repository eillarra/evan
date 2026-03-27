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

      <evan-section-title>Privacy</evan-section-title>
      <q-list dense>
        <q-item tag="label">
          <q-item-section avatar>
            <q-checkbox v-model="allowContact" keep-color />
          </q-item-section>
          <q-item-section>
            <q-item-label>Allow other attendees to contact me</q-item-label>
            <q-item-label caption
              >Attendees can send you messages through our internal contact form.
              <strong>We will never share your email directly.</strong></q-item-label
            >
          </q-item-section>
        </q-item>
      </q-list>

      <ugent-btn
        @click="saveProfile"
        :label="$t('form.update')"
        color="primary"
        class="q-mt-xl"
        :disable="!formIsValid || loading"
        :loading="loading"
      />
      <q-space class="q-mb-xl" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, triggerRef } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';

import { notify } from '@/utils/notify';
import { useUserStore } from '@/stores/user';

import CountrySelect from '@/components/CountrySelect.vue';
import DietarySelect from '@/components/DietarySelect.vue';
import GenderSelect from '@/components/GenderSelect.vue';
import EvanSectionTitle from '@/components/EvanSectionTitle.vue';

const { t } = useI18n();
const userStore = useUserStore();

const { user } = storeToRefs(userStore);
const loading = ref<boolean>(false);

const allowContact = computed<boolean>({
  get: () => user.value?.extra_data?.connect ?? false,
  set: (value: boolean) => {
    if (user.value) {
      if (!user.value.extra_data) {
        user.value.extra_data = {};
      }
      user.value.extra_data.connect = value;
      triggerRef(user); // Force shallowRef to notify reactivity
    }
  },
});

async function saveProfile() {
  if (user.value) {
    loading.value = true;
    try {
      await userStore.updateUser({
        first_name: user.value.first_name,
        last_name: user.value.last_name,
        affiliation: user.value.affiliation,
        country: user.value.country,
        extra_data: user.value.extra_data,
      });
      notify.success(t('messages.profile_updated'));
    } finally {
      loading.value = false;
    }
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
