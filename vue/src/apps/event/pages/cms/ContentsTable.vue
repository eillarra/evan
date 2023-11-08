<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="notes"
    :form-component="ContentForm"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import DataTable from '@/components/tables/DataTable.vue';
import ContentForm from './ContentForm.vue';

const { t } = useI18n();

const props = defineProps<{
  contents: Content[];
}>();

const queryColumns = ['key'];

const columns = [
  {
    name: 'key',
    field: 'key',
    required: true,
    label: t('fields.code'),
    align: 'left',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
];

const rows = computed(() => {
  return props.contents.map((obj: Content) => ({
    _self: obj,
    key: obj.key,
  }));
});
</script>
