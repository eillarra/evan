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

const queryColumns = ['code', 'title', 'session_code'];

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
    name: 'session',
    field: 'session_code',
    label: t('models.session_code'),
    align: 'left',
    autoWidth: true,
    sortable: true,
  },
];

const rows = computed(() => {
  return props.papers.map((obj: Paper) => {
    // Find the session for this paper
    const session = obj.session ? store.sessions.find((s) => s.id === obj.session) : null;

    return {
      _self: obj,
      title: obj.title,
      session_code: session?.code || '-',
    };
  });
});

function removePaper(row: { _self: Paper }) {
  store.removePaper(row._self);
}
</script>
