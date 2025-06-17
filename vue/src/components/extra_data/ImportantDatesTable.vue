<template>
  <div class="flex justify-between q-gutter-sm q-mb-lg">
    <div v-if="$slots.banner">
      <warning-banner type="warning">
        <slot name="banner" />
      </warning-banner>
    </div>
    <div class="ugent__create-btn">
      <q-btn
        unelevated
        color="blue-1"
        :label="$t('form.new')"
        :icon="iconAdd"
        class="text-ugent"
        @click="dialog = true"
      />
    </div>
  </div>
  <data-table
    :columns="columns"
    :rows="rows"
    :form-component="ImportantDateForm"
    :updateCallback="updateDate"
    removable
    @remove:row="removeDate"
    hide-toolbar
  />
  <q-dialog v-model="dialog">
    <important-date-form @create:obj="createDate" />
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import DataTable from '@/components/tables/DataTable.vue';
import ImportantDateForm from './ImportantDateForm.vue';
import WarningBanner from '@/components/ui/WarningBanner.vue';

import { iconAdd } from '@/icons';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: ApiObjectWithDates;
  updateCallback: (data: EvanEventExtraData | SessionExtraData) => Promise<void>;
}>();

const { t } = useI18n();

const dialog = ref(false);
const mutable = ref<ApiObjectWithDates>(props.modelValue as ApiObjectWithDates);
const columns = [
  {
    name: 'label',
    field: 'label',
    required: true,
    label: t('fields.label'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'start_date',
    field: 'start_date',
    label: t('fields.start_date'),
    align: 'left',
    autoWidth: true,
  },
  {
    name: 'end_date',
    field: 'end_date',
    label: t('fields.end_date'),
    align: 'left',
    autoWidth: true,
  },
  {
    name: 'format',
    field: 'format',
    label: t('fields.format'),
    align: 'left',
    autoWidth: true,
  },
  {
    name: 'is_aoe',
    field: 'is_aoe',
    label: 'AoE',
    align: 'center',
    autoWidth: true,
  },
];

const rows = computed(() => {
  return props.modelValue.extra_data.important_dates.map((obj: ImportantDate) => ({
    _self: obj,
    label: obj.label,
    start_date: obj.start_date,
    end_date: obj.end_date || '-',
    format: obj.format,
    is_aoe: obj.aoe,
  }));
});

function syncDates() {
  mutable.value.extra_data.important_dates.sort((a: ImportantDate, b: ImportantDate) => {
    return a.start_date.localeCompare(b.start_date);
  });

  return props.updateCallback(mutable.value.extra_data).then(() => {
    emit('update:modelValue', mutable.value);
  });
}

function createDate(obj: ImportantDate) {
  mutable.value.extra_data.important_dates.push(obj);
  syncDates().then(() => {
    notify.success(t('messages.important_date_created'));
  });
  dialog.value = false;
}

function updateDate(oldDate: ImportantDate, date: ImportantDate) {
  const index = mutable.value.extra_data.important_dates.findIndex(
    (d: ImportantDate) => d.label === oldDate.label && d.start_date === oldDate.start_date,
  );
  if (index !== -1) {
    mutable.value.extra_data.important_dates[index] = date as ImportantDate;
    syncDates().then(() => {
      notify.success(t('messages.important_date_updated'));
    });
  }
}

function removeDate(row: { _self: ImportantDate }) {
  confirm(t('messages.important_date_confirm_delete'), () => {
    mutable.value.extra_data.important_dates = mutable.value.extra_data.important_dates.filter(
      (date: ImportantDate) => date !== row._self,
    );
    syncDates().then(() => {
      notify.success(t('messages.important_date_deleted'));
    });
  });
}
</script>
