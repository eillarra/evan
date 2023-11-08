<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    :hidden-columns="hiddenColumns"
    :form-component="RegistrationDialog"
    sort-by="-date"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { formatDate } from '@/utils/dates';

import DataTable from '@/components/tables/DataTable.vue';
import RegistrationDialog from './RegistrationDialog.vue';

const { t } = useI18n();

const props = defineProps<{
  registrations: Registration[];
}>();

const queryColumns = ['name', 'affiliation', 'code'];
const hiddenColumns = ['uuid'];

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
    name: 'is_paid',
    field: 'is_paid',
    label: t('fields.paid'),
    align: 'center',
  },
];

const rows = computed(() => {
  return props.registrations.map((obj: Registration) => ({
    _self: obj,
    remarks: Number(obj.tag_objects?.['remarks.count']) || 0,
    name: obj.user.name,
    affiliation: obj.user.affiliation || '-',
    email: obj.user.email,
    uuid: obj.uuid,
    date: formatDate(obj.created_at),
    is_paid: obj.is_paid,
  }));
});
</script>
