<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="notes"
    :form-component="PaperForm"
    :create-form-component="PaperForm"
    removable
    @remove:row="removePaper"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import PaperForm from './PaperForm.vue';

const props = defineProps<{
  papers: Paper[];
}>();

const store = useStore();
const { t } = useI18n();

const queryColumns = ['code', 'title'];

const columns = [
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
    name: 'authors',
    field: 'authors',
    label: t('fields.author', 9),
    align: 'right',
    autoWidth: true,
  },
];

const rows = computed(() => {
  return props.papers.map((obj: Paper) => ({
    _self: obj,
    title: obj.title,
    authors: 'TODO',
  }));
});

function removePaper(row: { _self: Paper }) {
  store.removePaper(row._self);
}
</script>
