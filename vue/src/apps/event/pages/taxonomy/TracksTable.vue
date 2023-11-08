<template>
  <data-table
    :columns="columns"
    :rows="rows"
    sort-by="notes"
    :form-component="TrackForm"
    removable
    @remove:row="removeTrack"
    hide-pagination
    hide-toolbar
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store.js';

import DataTable from '@/components/tables/DataTable.vue';
import TrackForm from './TrackForm.vue';

const props = defineProps<{
  tracks: Track[];
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
  return props.tracks.map((obj: Track) => ({
    _self: obj,
    name: obj.name,
  }));
});

function removeTrack(row: { _self: Track }) {
  store.removeTrack(row._self);
}
</script>
