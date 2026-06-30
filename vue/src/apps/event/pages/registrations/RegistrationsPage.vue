<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.registration', 9) }}
      <q-icon
        v-if="registrationsExcelUrl"
        tag="a"
        :href="registrationsExcelUrl"
        target="_blank"
        :name="iconDownloadExcel"
        size="sm"
        color="grey-7"
        class="cursor-pointer q-ml-sm"
      >
        <q-tooltip :delay="250">{{ $t('registrations.download_excel') }}</q-tooltip>
      </q-icon>
    </h3>
    <div class="col"></div>
    <q-select
      v-show="feeOptions.length > 1"
      v-model="selectedFee"
      :options="feeOptions"
      clearable
      dense
      rounded
      outlined
      :label="$t('models.fee_type')"
      options-dense
      emit-value
      map-options
      class="col-6 col-md-2"
      :bg-color="selectedFee !== null ? 'blue-1' : 'white'"
    >
      <template #selected-item="scope">
        <span class="ellipsis">{{ scope.opt.label }}</span>
      </template>
      <template v-slot:option="{ itemProps, opt }">
        <q-item v-bind="itemProps">
          <q-item-section>
            <q-item-label>{{ opt.label }}</q-item-label>
            <q-item-label caption>{{ opt.description }}</q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-select>
    <q-select
      v-show="registrations.length > 1"
      v-model="selectedPaid"
      :options="paidOptions"
      clearable
      dense
      rounded
      outlined
      :label="$t('payment_status')"
      options-dense
      emit-value
      map-options
      class="col-6 col-md-2"
      :bg-color="selectedPaid !== null ? 'blue-1' : 'white'"
    >
      <template #selected-item="scope">
        <span class="ellipsis">{{ scope.opt.label }}</span>
      </template>
    </q-select>
  </div>
  <registrations-table
    :registrations="filteredRegistrations"
    :preview-form-url="evanEvent?.registration_preview_url || null"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { iconDownloadExcel } from '@/icons';
import { useStore } from '../../store';

import RegistrationsTable from './RegistrationsTable.vue';

const store = useStore();

const { evanEvent, registrations } = storeToRefs(store);

const selectedFee = ref<string | null>(null);
const selectedPaid = ref<string | null>(null);

const feeOptions = computed<QuasarSelectOption[]>(() => {
  if (!evanEvent.value || !evanEvent.value.fees.length || !registrations.value.length) {
    return [];
  }

  const fees: string[] = [];

  registrations.value.forEach((registration) => {
    if (registration.fee_type) {
      fees.push(registration.fee_type);
    }
  });

  return evanEvent.value.fees
    .filter((fee) => fees.includes(fee.type))
    .map((fee) => {
      return { label: fee.type, value: fee.type, description: fee.notes };
    });
});

const paidOptions = computed<QuasarSelectOption[]>(() => [
  { label: 'Paid', value: 'paid' },
  { label: 'Paid, using a coupon', value: 'paid_coupon' },
  { label: 'Not paid, no invoice', value: 'not_paid_no_invoice' },
  { label: 'Not paid, but requested invoice', value: 'not_paid_invoice_requested' },
]);

const registrationsExcelUrl = computed<string | null>(() => {
  if (!evanEvent.value?.code) {
    return null;
  }

  return `/e/${evanEvent.value.code}/files/registrations.xlsx`;
});

const filteredRegistrations = computed<Registration[]>(() => {
  return registrations.value
    .filter((obj) => {
      if (selectedPaid.value === null) return true;

      if (selectedPaid.value === 'paid') {
        return obj.is_paid;
      } else if (selectedPaid.value === 'paid_coupon') {
        return obj.is_paid && obj.coupon;
      } else if (selectedPaid.value === 'not_paid_no_invoice') {
        return !obj.is_paid && !obj.invoice_requested;
      } else if (selectedPaid.value === 'not_paid_invoice_requested') {
        return !obj.is_paid && obj.invoice_requested;
      }

      return false;
    })
    .filter((obj) => selectedFee.value === null || obj.fee_type === selectedFee.value);
});
</script>
