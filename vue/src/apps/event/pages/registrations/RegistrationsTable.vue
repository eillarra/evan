<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    :hidden-columns="hiddenColumns"
    sort-by="-date"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { formatCurrency } from '@/utils/numbers';
import { formatDate } from '@/utils/dates';

import DataTable from '@/components/tables/DataTable.vue';
// import RegistrationDialog from './RegistrationDialog.vue';

const { t } = useI18n();

const props = defineProps<{
  registrations: Registration[];
}>();

const queryColumns = ['name', 'affiliation', 'uuid', 'email'];
const hiddenColumns = ['uuid', 'has_coupon'];

const columns = [
  {
    name: 'remarks',
    field: 'remarks',
    required: true,
    label: null,
    align: 'left',
    autoWidth: true,
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'name',
    field: 'name',
    required: true,
    label: t('fields.name'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'affiliation',
    field: 'affiliation',
    label: t('fields.affiliation'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'email',
    field: 'email',
    label: t('fields.email'),
    align: 'left',
    sortable: true,
  },
  {
    name: 'uuid',
    field: 'uuid',
    label: t('fields.code'),
    align: 'left',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'date',
    field: 'date',
    label: t('fields.date'),
    align: 'left',
    autoWidth: true,
    sortable: true,
  },
  {
    name: 'fee_type',
    field: 'fee_type',
    label: t('models.fee_type'),
    align: 'left',
  },
  {
    name: 'total_fee',
    field: 'total_fee',
    label: t('fields.fee'),
    align: 'right',
    classes: 'panno-mono-number',
  },
  {
    name: 'is_paid',
    field: 'is_paid',
    label: t('fields.paid'),
    align: 'center',
  },
  {
    name: 'has_coupon',
    field: 'has_coupon',
    label: t('models.coupon'),
    align: 'center',
  },
];

const rows = computed(() => {
  return props.registrations.map((obj: Registration) => ({
    _self: obj,
    _remarks_endpoint: obj.rel_remarks,
    _remarks_title: obj.user.name,
    remarks: Number(obj._tags_dict?.['remarks.count']) || 0,
    name: obj.user.name,
    affiliation: obj.user.affiliation || '-',
    email: obj.user.email,
    uuid: obj.uuid,
    date: formatDate(obj.created_at),
    fee_type: obj.fee_type || '-',
    total_fee: formatCurrency(obj.total_fee),
    is_paid: obj.is_paid ? true : obj.paid > 0 || obj.paid_via_invoice > 0 || obj.coupon ? null : false,
    has_coupon: !!obj.coupon,
  }));
});
</script>
