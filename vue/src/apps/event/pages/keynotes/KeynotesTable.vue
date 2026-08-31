<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="code"
    :form-component="KeynoteForm"
    :create-form-component="KeynoteForm"
    removable
    @remove:row="removeKeynote"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import KeynoteForm from './KeynoteForm.vue';

const props = defineProps<{
  keynotes: Keynote[];
}>();

const store = useStore();
const { t } = useI18n();

const queryColumns = ['code', 'title', 'speaker', 'session_code'];

const columns = [
  {
    name: 'code',
    field: 'code',
    required: true,
    label: t('fields.code'),
    align: 'left',
    autoWidth: true,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
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
    name: 'speaker',
    field: 'speaker',
    label: t('fields.speaker'),
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
  return props.keynotes.map((obj: Keynote) => {
    // Find the session for this keynote
    const session = obj.session ? store.sessions.find((s) => s.id === obj.session) : null;

    return {
      _self: obj,
      code: obj.code,
      title: obj.title,
      speaker: obj.speaker,
      session_code: session?.code || '-',
    };
  });
});

function removeKeynote(row: { _self: Keynote }) {
  store.removeKeynote(row._self);
}
</script>
