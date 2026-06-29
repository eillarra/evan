<template>
  <div class="row q-col-gutter-x-xl">
    <h3 class="text-ugent col-12">My profile</h3>
    <div v-if="user" class="col-12 col-md-7">
      <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
        <profile-info-fields v-model:user="user" class="col-12" />
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
import { normalizeNameIfAllCaps } from '@/utils/nameNormalization';

import DietarySelect from '@/components/DietarySelect.vue';
import EvanSectionTitle from '@/components/EvanSectionTitle.vue';
import ProfileInfoFields from '../components/ProfileInfoFields.vue';

const defaultUserExtraData = (): UserExtraData => ({
  gender: '',
  dietary: 'none',
  special_needs: null,
  connect: false,
});

const { t } = useI18n();
const userStore = useUserStore();

const { user } = storeToRefs(userStore);
const loading = ref<boolean>(false);

const allowContact = computed<boolean>({
  get: () => user.value?.extra_data?.connect ?? false,
  set: (value: boolean) => {
    if (user.value) {
      const extraData = user.value.extra_data ? { ...user.value.extra_data } : defaultUserExtraData();
      extraData.connect = value;
      user.value = {
        ...user.value,
        extra_data: extraData,
      };
      triggerRef(user);
    }
  },
});

async function saveProfile() {
  if (user.value) {
    loading.value = true;
    try {
      const firstName = normalizeNameIfAllCaps(user.value.first_name || '');
      const lastName = normalizeNameIfAllCaps(user.value.last_name || '');
      const extraData = user.value.extra_data ? { ...user.value.extra_data } : defaultUserExtraData();

      user.value = {
        ...user.value,
        first_name: firstName,
        last_name: lastName,
        extra_data: extraData,
      };

      await userStore.updateUser({
        first_name: firstName,
        last_name: lastName,
        affiliation: user.value.affiliation,
        country: user.value.country,
        extra_data: extraData,
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
