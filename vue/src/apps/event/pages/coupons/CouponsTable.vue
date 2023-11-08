<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="notes"
    :form-component="CouponForm"
    :create-form-component="CouponForm"
    removable
    @remove:row="removeCoupon"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store.js';

import DataTable from '@/components/tables/DataTable.vue';
import CouponForm from './CouponForm.vue';

const props = defineProps<{
  coupons: Coupon[];
  couponIdsUsed: Set<number>;
}>();

const store = useStore();
const { t } = useI18n();

const queryColumns = ['code', 'notes'];
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
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'value',
    field: 'value',
    label: t('fields.value'),
    align: 'right',
    autoWidth: true,
    sortable: true,
    classes: 'panno-mono-number',
  },
  {
    name: 'notes',
    field: 'notes',
    label: t('fields.note', 9),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'is_used',
    field: 'is_used',
    label: t('fields.used'),
    align: 'center',
  },
];

const rows = computed(() => {
  return props.coupons.map((obj: Coupon) => ({
    _self: obj,
    code: obj.code,
    value: obj.value,
    notes: obj.notes,
    is_used: props.couponIdsUsed.has(obj.id),
  }));
});

function removeCoupon(row: { _self: Coupon }) {
  store.removeCoupon(row._self);
}
</script>
