<template>
  <data-table
    :columns="columns"
    :rows="rows"
    sort-by="notes"
    :form-component="TopicForm"
    removable
    @remove:row="removeTopic"
    hide-pagination
    hide-toolbar
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store.js';

import DataTable from '@/components/tables/DataTable.vue';
import TopicForm from './TopicForm.vue';

const props = defineProps<{
  topics: Topic[];
}>();

const { t } = useI18n();
const store = useStore();

const columns = [
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
];

const rows = computed(() => {
  return props.topics.map((obj: Topic) => ({
    _self: obj,
    name: obj.name,
  }));
});

function removeTopic(row: { _self: Topic }) {
  store.removeTopic(row._self);
}
</script>
