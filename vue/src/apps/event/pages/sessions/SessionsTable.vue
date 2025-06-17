<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="date"
    :form-component="SessionForm"
    :create-form-component="SessionForm"
    removable
    @remove:row="removeSession"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import SessionForm from './SessionForm.vue';

const props = defineProps<{
  sessions: Session[];
}>();

const store = useStore();
const { t } = useI18n();

const queryColumns = ['code', 'title'];

const columns = [
  {
    name: 'code',
    field: 'code',
    label: t('fields.code'),
    align: 'left',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'title',
    field: 'title',
    required: true,
    label: t('fields.title'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'subsessions',
    field: 'subsessions',
    label: t('models.subsession', 9),
    align: 'center',
    autoWidth: true,
    sortable: true,
    format: (val: number) => (val > 0 ? val.toString() : '-'),
  },
  {
    name: 'date',
    field: 'date',
    label: t('fields.date'),
    align: 'right',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'start_time',
    field: 'start_time',
    label: t('fields.start_time'),
    align: 'right',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'end_time',
    field: 'end_time',
    label: t('fields.end_time'),
    align: 'right',
    autoWidth: true,
    sortable: true,
  },
];

const rows = computed(() => {
  return props.sessions.map((obj: Session) => ({
    _self: obj,
    code: obj.code || '-',
    title: obj.title,
    subsessions: obj.subsessions?.length || 0,
    date: obj.start_at ? new Date(obj.start_at).toLocaleDateString('en-BE') : '-',
    start_time: obj.start_at ? new Date(obj.start_at).toLocaleTimeString('en-BE', { timeStyle: 'short' }) : '-',
    end_time: obj.end_at ? new Date(obj.end_at).toLocaleTimeString('en-BE', { timeStyle: 'short' }) : '-',
  }));
});

function removeSession(row: { _self: Session }) {
  store.removeSession(row._self);
}
</script>
