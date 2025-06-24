<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="name"
    :form-component="VenueForm"
    :create-form-component="VenueForm"
    removable
    @remove:row="removeVenue"
  >
    <template #body-cell-website="props">
      <q-td :props="props">
        <a v-if="props.value" :href="props.value" target="_blank" class="text-primary">
          <q-icon name="language" size="sm" class="q-mr-xs" />
          {{ truncateUrl(props.value) }}
        </a>
        <span v-else class="text-grey-5">—</span>
      </q-td>
    </template>

    <template #body-cell-google_place_id="props">
      <q-td :props="props">
        <a
          v-if="props.value"
          :href="`https://www.google.com/maps/place/?q=place_id:${props.value}`"
          target="_blank"
          class="text-primary"
        >
          <q-icon name="place" size="sm" class="q-mr-xs" />
          {{ truncateText(props.value) }}
        </a>
        <span v-else class="text-grey-5">—</span>
      </q-td>
    </template>
  </data-table>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import VenueForm from './VenueForm.vue';

const props = defineProps<{
  venues: Venue[];
}>();

const { t } = useI18n();
const store = useStore();

const queryColumns = ['name', 'city', 'website', 'google_place_id', 'room_names'];

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
    name: 'city',
    field: 'city',
    label: t('fields.city'),
    align: 'left',
    sortable: true,
    autoWidth: true,
  },
  {
    name: 'website',
    field: 'website',
    label: t('fields.website'),
    align: 'left',
    sortable: true,
    autoWidth: true,
  },
  {
    name: 'google_place_id',
    field: 'google_place_id',
    label: t('fields.google_place_id'),
    align: 'left',
    sortable: true,
    autoWidth: true,
  },
  {
    name: 'rooms_count',
    field: 'rooms_count',
    label: t('models.room', 9),
    align: 'center',
    autoWidth: true,
    sortable: true,
  },
  {
    name: 'is_main',
    field: 'is_main',
    label: t('fields.is_main'),
    align: 'center',
    autoWidth: true,
    sortable: true,
  },
];

const rows = computed(() => {
  return props.venues.map((obj: Venue) => ({
    _self: obj,
    name: obj.name,
    city: obj.city,
    website: obj.website,
    google_place_id: obj.google_place_id,
    rooms_count: obj.rooms.length,
    is_main: obj.is_main,
    room_names: obj.rooms.map((room) => room.name).join(' '),
  }));
});

function removeVenue(row: { _self: Venue }) {
  store.removeVenue(row._self);
}

function truncateUrl(url: string): string {
  if (!url) return '';
  try {
    const domain = new URL(url).hostname.replace('www.', '');
    return domain.length > 25 ? domain.substring(0, 22) + '...' : domain;
  } catch {
    return url.length > 25 ? url.substring(0, 22) + '...' : url;
  }
}

function truncateText(text: string): string {
  if (!text) return '';
  return text.length > 20 ? text.substring(0, 17) + '...' : text;
}
</script>
