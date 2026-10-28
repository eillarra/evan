<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="level"
    :form-component="SponsorForm"
    :create-form-component="SponsorForm"
    removable
    @remove:row="removeSponsor"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DataTable from '@/components/tables/DataTable.vue';
import SponsorForm from './SponsorForm.vue';

const props = defineProps<{
  sponsors: Sponsor[];
}>();

const store = useStore();
const { sponsorTypeOptions } = storeToRefs(store);
const { t } = useI18n();

const queryColumns = ['name', 'website'];

// The column displays the configured tier label, so sorting on that label alone
// would order tiers alphabetically instead of by the configured tier order.
function sortByConfiguredLevel(a: string | number, b: string | number): number {
  const options = sponsorTypeOptions.value;
  const rankA = options.findIndex((option) => option.label === a);
  const rankB = options.findIndex((option) => option.label === b);

  return rankA !== -1 && rankB !== -1
    ? rankA - rankB
    : String(a).localeCompare(String(b), undefined, { numeric: true });
}

const columns = [
  {
    name: 'name',
    field: 'name',
    required: true,
    label: t('fields.name'),
    align: 'left' as const,
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'website',
    field: 'website',
    label: t('fields.website'),
    align: 'left' as const,
  },
  {
    name: 'level',
    field: 'level',
    label: sponsorTypeOptions.value.length ? t('fields.type') : t('fields.order'),
    align: 'right' as const,
    autoWidth: true,
    sortable: true,
    sort: sortByConfiguredLevel,
  },
  {
    name: 'has_logo',
    field: 'has_logo',
    label: 'Logo',
    align: 'center' as const,
    autoWidth: true,
  },
];

const rows = computed(() => {
  return props.sponsors.map((obj: Sponsor) => ({
    _self: obj,
    name: obj.name,
    website: obj.website,
    level: sponsorTypeOptions.value.find((o) => o.value === obj.level)?.label ?? obj.level,
    has_logo: obj.files.length > 0,
  }));
});

function removeSponsor(row: { _self: Sponsor }) {
  store.removeSponsor(row._self);
}
</script>
