<template>
  <div class="row q-col-gutter-sm q-mb-md">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.event') }}
    </h3>
  </div>
  <div v-if="evanEvent">
    <q-tabs v-model="activeTab" dense narrow-indicator no-caps align="left" style="margin-left: -16px">
      <q-tab name="general" :label="$t('tabs.general')" />
      <q-tab name="registration" :label="$t('event.registration')" />
      <q-tab name="badges" :label="$t('event.badges')" />
    </q-tabs>
    <q-tab-panels v-model="activeTab">
      <q-tab-panel name="general" class="q-px-none">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <readonly-field :value="evanEvent.code" :label="$t('fields.code')" class="col-12 col-md-4" />
          <q-input v-model="evanEvent.website" :label="$t('fields.website')" dense class="col-12 col-md-8" />
          <q-input v-model="evanEvent.name" :label="$t('fields.name')" dense class="col-12 col-md-4" />
          <q-input v-model="evanEvent.full_name" :label="$t('fields.full_name')" dense class="col-12 col-md-8" />
          <q-input v-model="evanEvent.city" :label="$t('fields.city')" dense class="col-12 col-md-4" />
          <country-select v-model="evanEvent.country" :label="$t('fields.country')" class="col-12 col-md-4" as-dict />
          <q-input v-model="evanEvent.hashtag" :label="$t('fields.hashtag')" dense class="col-12 col-md-4" />
          <date-select
            v-model="evanEvent.start_date"
            type="date"
            :label="$t('fields.start_date')"
            class="col-12 col-md-4"
          />
          <date-select
            v-model="evanEvent.end_date"
            type="date"
            :label="$t('fields.end_date')"
            class="col-12 col-md-4"
          />
          <marked-textarea v-model="evanEvent.presentation" :label="$t('fields.presentation')" class="col-12" />
          <q-input v-model="evanEvent.email" :label="$t('fields.email')" type="email" dense class="col-12 col-md-4" />
        </div>
        <div class="row items-center q-mt-md">
          <div class="col"></div>
          <div class="col-auto">
            <q-btn unelevated @click="updateGeneral" color="ugent" :label="$t('form.update')" :loading="generalLoading" />
          </div>
        </div>
      </q-tab-panel>
      <q-tab-panel name="registration" class="q-px-none">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <readonly-field
            :value="evanEvent.is_virtual ? 'Yes' : 'No'"
            :label="$t('event.is_virtual')"
            class="col-12 col-md-3"
          />
          <readonly-field
            :value="evanEvent.is_open_for_registration ? 'Yes' : 'No'"
            :label="$t('event.is_open_for_registration')"
            class="col-12 col-md-3"
          />
          <readonly-field
            :value="evanEvent.accept_by_default ? 'Yes' : 'No'"
            :label="$t('event.accept_by_default')"
            class="col-12 col-md-3"
          />
          <readonly-field
            :value="evanEvent.registrations_count"
            :label="$t('event.registration_count')"
            class="col-12 col-md-3"
          />
          <date-select
            v-model="evanEvent.registration_start_date"
            type="date"
            :label="$t('fields.registration_start_date')"
            class="col-12 col-md-4"
          />
          <date-select
            v-model="evanEvent.registration_early_deadline"
            type="datetime"
            :label="$t('fields.registration_early_deadline')"
            class="col-12 col-md-4"
            clearable
          />
          <date-select
            v-model="evanEvent.registration_deadline"
            type="datetime"
            :label="$t('fields.registration_deadline')"
            class="col-12 col-md-4"
          />
          <marked-textarea v-model="evanEvent.signature" :label="$t('fields.visa_signature')" class="col-12" />
        </div>
        <div class="row items-center q-mt-md">
          <div class="col"></div>
          <div class="col-auto">
            <q-btn
              unelevated
              @click="updateRegistration"
              color="ugent"
              :label="$t('form.update')"
              :loading="registrationLoading"
            />
          </div>
        </div>
      </q-tab-panel>
      <q-tab-panel name="badges" class="q-px-none">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <color-input
            v-model="badgeConfigDefault"
            :label="$t('badges.default_badge_color')"
            dense
            class="col-12 col-md-6"
          />
          <color-input
            v-model="badgeConfigGuest"
            :label="$t('badges.guest_badge_color')"
            dense
            class="col-12 col-md-6"
          />
          <div class="col-12">
            <div class="text-subtitle2 q-mb-sm">{{ $t('badges.fee_type_colors') }}</div>
            <div v-if="evanEvent?.fees?.length" class="q-mb-md">
              <div v-for="fee in evanEvent.fees" :key="fee.type" class="row q-col-gutter-sm q-mb-sm items-top">
                <div class="col-6">
                  <q-input :model-value="fee.type" :label="$t('badges.fee_type')" dense readonly />
                  <div class="text-caption text-grey-6">{{ fee.notes }}</div>
                </div>
                <div class="col-6">
                  <color-input
                    :model-value="feeTypeColors[fee.type] || badgeConfigDefault"
                    @update:model-value="(value) => updateFeeTypeColor(fee.type, value)"
                    :label="$t('badges.color')"
                    dense
                    :clearable="isFeeColorCustom(fee.type)"
                  />
                </div>
              </div>
            </div>
            <div v-else class="text-grey-6 text-center q-py-md">
              {{ $t('badges.no_fee_types_available') }}
            </div>
          </div>
          <div class="col-12 q-mt-md">
            <div class="text-subtitle2 q-mb-sm">{{ $t('badges.preview') }}</div>
            <div class="row q-col-gutter-sm">
              <div class="col-sm-6 col-md">
                <div class="text-center text-white q-pa-md" :style="{ backgroundColor: badgeConfigDefault }">
                  {{ $t('badges.default') }}
                </div>
              </div>
              <div class="col-sm-6 col-md">
                <div class="text-center text-white q-pa-md" :style="{ backgroundColor: badgeConfigGuest }">
                  {{ $t('badges.guest') }}
                </div>
              </div>
              <div v-for="fee in evanEvent.fees" :key="`preview-${fee.type}`" class="col-sm-6 col-md">
                <div
                  :style="{ backgroundColor: feeTypeColors[fee.type] || badgeConfigDefault }"
                  class="text-center text-white q-pa-md"
                >
                  {{ fee.type }}
                </div>
              </div>
            </div>
            <div class="row items-center q-mt-xl">
              <div class="col-auto">
                <q-btn
                  outline
                  color="ugent"
                  :label="$t('badges.download_badge_pdf')"
                  @click="downloadBadgePdf"
                  :loading="pdfLoading"
                />
              </div>
              <div class="col"></div>
              <div class="col-auto">
                <q-btn unelevated @click="updateBadges" color="ugent" :label="$t('form.update')" :loading="badgesLoading" />
              </div>
            </div>
          </div>
        </div>
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import ColorInput from '@/components/forms/ColorInput.vue';
import CountrySelect from '@/components/CountrySelect.vue';
import DateSelect from '@/components/forms/DateSelect.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

const store = useStore();
const { evanEvent } = storeToRefs(store);

const activeTab = ref('general');
const pdfLoading = ref(false);
const generalLoading = ref(false);
const registrationLoading = ref(false);
const badgesLoading = ref(false);

const feeTypeColors = computed({
  get: () => evanEvent.value?.extra_data?.badges?.fee_colors ?? {},
  set: (value: Record<string, string>) => {
    if (evanEvent.value) {
      if (!evanEvent.value.extra_data) {
        evanEvent.value.extra_data = {
          badges: { default: '#2196F3', guest: '#4CAF50', fee_colors: value },
          important_dates: [],
        };
      } else if (!evanEvent.value.extra_data.badges) {
        evanEvent.value.extra_data.badges = { default: '#2196F3', guest: '#4CAF50', fee_colors: value };
      } else {
        evanEvent.value.extra_data.badges.fee_colors = value;
      }
    }
  },
});

const badgeConfigDefault = computed({
  get: () => evanEvent.value?.extra_data?.badges?.default ?? '#2196F3',
  set: (value: string) => {
    if (evanEvent.value) {
      if (!evanEvent.value.extra_data) {
        evanEvent.value.extra_data = {
          badges: { default: value, guest: '#4CAF50', fee_colors: {} },
          important_dates: [],
        };
      } else if (!evanEvent.value.extra_data.badges) {
        evanEvent.value.extra_data.badges = { default: value, guest: '#4CAF50', fee_colors: {} };
      } else {
        evanEvent.value.extra_data.badges.default = value;
      }
    }
  },
});

const badgeConfigGuest = computed({
  get: () => evanEvent.value?.extra_data?.badges?.guest ?? '#4CAF50',
  set: (value: string) => {
    if (evanEvent.value) {
      if (!evanEvent.value.extra_data) {
        evanEvent.value.extra_data = {
          badges: { default: '#2196F3', guest: value, fee_colors: {} },
          important_dates: [],
        };
      } else if (!evanEvent.value.extra_data.badges) {
        evanEvent.value.extra_data.badges = { default: '#2196F3', guest: value, fee_colors: {} };
      } else {
        evanEvent.value.extra_data.badges.guest = value;
      }
    }
  },
});

function updateFeeTypeColor(feeType: string, color: string) {
  const currentColors = { ...feeTypeColors.value };
  if (!color || color === '') {
    delete currentColors[feeType];
  } else if (color === badgeConfigDefault.value) {
    delete currentColors[feeType];
  } else {
    currentColors[feeType] = color;
  }
  feeTypeColors.value = currentColors;
}

function isFeeColorCustom(feeType: string): boolean {
  return feeTypeColors.value[feeType] !== undefined;
}

async function downloadBadgePdf() {
  if (!evanEvent.value) return;

  pdfLoading.value = true;

  try {
    const response = await fetch(`/e/${evanEvent.value.code}/files/badges.pdf`);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${evanEvent.value.code}_badges.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } else {
      throw new Error('PDF download failed');
    }
  } catch (error) {
    console.error('Error downloading PDF:', error);
  } finally {
    pdfLoading.value = false;
  }
}

async function updateGeneral() {
  if (!evanEvent.value) return;

  generalLoading.value = true;
  try {
    const generalData = {
      website: evanEvent.value.website,
      name: evanEvent.value.name,
      full_name: evanEvent.value.full_name,
      city: evanEvent.value.city,
      country: evanEvent.value.country,
      hashtag: evanEvent.value.hashtag,
      start_date: evanEvent.value.start_date,
      end_date: evanEvent.value.end_date,
      presentation: evanEvent.value.presentation,
      email: evanEvent.value.email,
    };
    await store.updateEventPartial(generalData);
  } finally {
    generalLoading.value = false;
  }
}

async function updateRegistration() {
  if (!evanEvent.value) return;

  registrationLoading.value = true;
  try {
    const registrationData = {
      registration_start_date: evanEvent.value.registration_start_date,
      registration_early_deadline: evanEvent.value.registration_early_deadline,
      registration_deadline: evanEvent.value.registration_deadline,
      signature: evanEvent.value.signature,
    };
    await store.updateEventPartial(registrationData);
  } finally {
    registrationLoading.value = false;
  }
}

async function updateBadges() {
  if (!evanEvent.value) return;

  badgesLoading.value = true;
  try {
    const badgesData = {
      extra_data: evanEvent.value.extra_data,
    };
    await store.updateEventPartial(badgesData);
  } finally {
    badgesLoading.value = false;
  }
}
</script>
