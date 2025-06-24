<template>
  <data-table
    :columns="columns"
    :rows="rows"
    sort-by="position"
    :form-component="RoomForm"
    :create-parent="venue"
    removable
    @remove:row="removeRoom"
    hide-pagination
    hide-toolbar
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import RoomForm from './RoomForm.vue';

const props = defineProps<{
  rooms: Room[];
  venue: Venue;
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
  {
    name: 'max_capacity',
    field: 'max_capacity',
    label: t('fields.capacity'),
    align: 'right',
    sortable: true,
  },
  {
    name: 'position',
    field: 'position',
    label: t('fields.position'),
    align: 'right',
    sortable: true,
  },
];

const rows = computed(() => {
  return props.rooms.map((obj: Room) => ({
    _self: obj,
    _venue: props.venue,
    name: obj.name,
    max_capacity: obj.max_capacity,
    position: obj.position,
  }));
});

function removeRoom(row: { _self: Room }) {
  store.removeRoom(row._self);
}
</script>
